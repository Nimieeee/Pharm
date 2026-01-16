"""
Authentication service
Handles user authentication, JWT tokens, and password management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import bcrypt
import jwt
from jwt import InvalidTokenError
from fastapi import HTTPException, status
from supabase import Client

from app.core.config import settings
from app.models.user import User, UserCreate, UserInDB
from app.models.auth import Token, TokenData
from cachetools import TTLCache
from supabase import Client as SupabaseClient
from app.services.email import EmailService

# Cache user lookups for 60 seconds to avoid hitting DB on every request
_user_cache = TTLCache(maxsize=500, ttl=60)


class AuthService:
    """Authentication service"""
    
    def __init__(self, db: Client):
        self.db = db
        self.email_service = EmailService()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            is_admin: bool = payload.get("is_admin", False)
            
            if user_id is None or email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            return TokenData(user_id=user_id, email=email, is_admin=is_admin)
            
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = self.db.table("users").select("id").eq("email", user_data.email).execute()
            if existing_user.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = self.hash_password(user_data.password)
            
            # Create user record
            user_dict = user_data.dict(exclude={"password"})
            user_dict["password_hash"] = hashed_password
            
            # Generate verification code
            code = self.generate_verification_code()
            user_dict["verification_code"] = code
            user_dict["is_verified"] = False  # Default to unverified

            # Send email with code
            self.email_service.send_verification_email(user_data.email, code)
            
            
            result = self.db.table("users").insert(user_dict).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            user_record = result.data[0]
            return User(**user_record)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password"""
        try:
            # Get user by email
            result = self.db.table("users").select("*").eq("email", email).execute()
            
            if not result.data:
                return None
            
            user_data = result.data[0]
            user = UserInDB(**user_data)
            
            # Check if user is active
            if not user.is_active:
                return None
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                return None
            
            # Check verification (skip for admins or specific legacy users if needed)
            if not user.is_verified and not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email not verified"
                )
            
            
            # Pre-warm the cache so first authenticated request is fast
            cache_key = f"user:email:{email}"
            _user_cache[cache_key] = User(**user_data)
            
            return user
            
        except Exception:
            return None

    async def authenticate_google_user(self, email: str, google_id: str, first_name: str = "", last_name: str = "", avatar_url: str = "") -> UserInDB:
        """
        Authenticate or Register a user from Google Login.
        
        Verification of the Google token happens BEFORE calling this method
        (via Supabase or direct validation). This method trusts the email is verified.
        """
        try:
            # 1. Check if user already exists
            existing_user = await self.get_user_by_email(email)
            
            if existing_user:
                # If they exist, we just return them (linking is implicit by email)
                # We need the full UserInDB object though (with password_hash)
                result = self.db.table("users").select("*").eq("email", email).execute()
                if result.data:
                    user_data = result.data[0]
                    # Update metadata if missing
                    updates = {}
                    if not user_data.get('avatar_url') and avatar_url:
                        updates['avatar_url'] = avatar_url
                    
                    if updates:
                        self.db.table("users").update(updates).eq("id", user_data['id']).execute()
                        user_data.update(updates)
                        
                    return UserInDB(**user_data)
            
            # 2. If user does not exist, create them
            # We generate a random high-entropy password since they won't use it
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            random_pw = ''.join(secrets.choice(alphabet) for i in range(32))
            
            user_create = UserCreate(
                email=email,
                password=random_pw, # dummy password
                first_name=first_name,
                last_name=last_name,
                avatar_url=avatar_url
            )
            
            # Use existing register logic
            # This handles hashing the dummy password and inserting
            new_user = await self.register_user(user_create)
            
            # We need to return UserInDB for the endpoint to generate tokens
            # Retch to include internal fields
            result = self.db.table("users").select("*").eq("id", str(new_user.id)).execute()
            if result.data:
                 return UserInDB(**result.data[0])
                 
            raise Exception("Failed to retrieve new user")

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Google authentication failed: {str(e)}"
            )
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        try:
            result = self.db.table("users").select("*").eq("id", str(user_id)).execute()
            
            if not result.data:
                return None
            
            user_data = result.data[0]
            return User(**user_data)
            
        except Exception:
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (with caching)"""
        # Check cache first
        cache_key = f"user:email:{email}"
        if cache_key in _user_cache:
            return _user_cache[cache_key]
        
        try:
            result = self.db.table("users").select("*").eq("email", email).execute()
            
            if not result.data:
                return None
            
            user_data = result.data[0]
            user = User(**user_data)
            
            # Debug: Log user name
            print(f"👤 get_user_by_email: {email} -> first_name='{user.first_name}'")
            
            # Store in cache
            _user_cache[cache_key] = user
            return user
            
        except Exception:
            return None

    async def update_user(self, user_id: UUID, user_update: Dict[str, Any]) -> Optional[User]:
        """Update user record and invalidate cache"""
        try:
            # First get the user to get their email (for cache invalidation)
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Update user in DB
            result = self.db.table("users").update(user_update).eq("id", str(user_id)).execute()
            if not result.data:
                return None
            
            updated_user_data = result.data[0]
            updated_user = User(**updated_user_data)
            
            # Invalidate cache
            cache_keys = [f"user:email:{user.email}", f"user:email:{updated_user.email}"]
            for key in cache_keys:
                _user_cache.pop(key, None)
            
            return updated_user
        except Exception as e:
            print(f"Update error: {e}")
            return None
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user account permanently"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
                
            # Delete from DB
            self.db.table("users").delete().eq("id", str(user_id)).execute()
            
            # Invalidate cache
            cache_key = f"user:email:{user.email}"
            _user_cache.pop(cache_key, None)
            
            return True
        except Exception as e:
            print(f"Delete user error: {e}")
            return False

    async def create_tokens(self, user: UserInDB) -> Token:
        """Create access and refresh tokens for user"""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "is_admin": user.is_admin
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Create new access token from refresh token"""
        try:
            # Verify refresh token
            token_data = self.verify_token(refresh_token, "refresh")
            
            # Get current user data
            user = await self.get_user_by_id(UUID(token_data.user_id))
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new tokens
            user_in_db = UserInDB(
                id=user.id,
                email=user.email,
                password_hash="",  # Not needed for token creation
                first_name=user.first_name,
                last_name=user.last_name,
                is_admin=user.is_admin,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            return await self.create_tokens(user_in_db)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token"
            )
    
    async def create_admin_user(self) -> User:
        """Create default admin user if it doesn't exist"""
        try:
            # Check if admin user exists
            admin_user = await self.get_user_by_email(settings.ADMIN_EMAIL)
            if admin_user:
                return admin_user
            
            # Create admin user
            admin_data = UserCreate(
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                first_name="Admin",
                last_name="User"
            )
            
            # Hash password
            hashed_password = self.hash_password(admin_data.password)
            
            # Insert admin user with admin flag
            user_dict = admin_data.dict(exclude={"password"})
            user_dict["password_hash"] = hashed_password
            user_dict["is_admin"] = True
            
            result = self.db.table("users").insert(user_dict).execute()
            
            if not result.data:
                raise Exception("Failed to create admin user")
            
            user_record = result.data[0]
            return User(**user_record)
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            raise

    def generate_verification_code(self) -> str:
        """Generate 6-digit code"""
        import secrets
        return "".join(secrets.choice("0123456789") for _ in range(6))

    async def verify_user_email(self, email: str, code: str) -> bool:
        """Verify user email with code"""
        try:
            # Get user including verification code (not in User model usually, so query raw)
            result = self.db.table("users").select("*").eq("email", email).execute()
            
            if not result.data:
                return False
            
            user_data = result.data[0]
            
            # Check code
            # Allow "123456" as master code for testing if needed, or stick to strict
            if user_data.get("verification_code") != code:
                return False
            
            # Update to verified
            self.db.table("users").update({
                "is_verified": True,
                "verification_code": None # Clear code
            }).eq("id", user_data["id"]).execute()
            
            return True
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False

    async def request_password_reset(self, email: str, frontend_url: str = "https://pharmgpt.app") -> bool:
        """
        Initiate password reset flow:
        1. Verify email exists
        2. Generate reset token
        3. Send email with link
        """
        user = await self.get_user_by_email(email)
        if not user:
            # Silent failure to prevent user enumeration
            print(f"⚠️ Password reset requested for non-existent email: {email}")
            return True
            
        # Create reset token (short lived - 30 mins)
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "type": "reset"
        }
        
        # Create token valid for 30 minutes
        expiry = timedelta(minutes=30)
        reset_token = self.create_access_token(token_data, expires_delta=expiry)
        
        # Build link (assume frontend route /reset-password?token=...)
        # Handle trailing slash in base url
        base_url = frontend_url.rstrip("/")
        link = f"{base_url}/reset-password?token={reset_token}"
        
        # Send email
        return self.email_service.send_password_reset_email(email, link)

    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset user password using token
        """
        try:
            # Verify token explicitly checking for 'reset' type
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            if payload.get("type") != "reset":
                raise HTTPException(status_code=400, detail="Invalid token type")
                
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=400, detail="Invalid token")
                
            # Hash new password
            hashed_password = self.hash_password(new_password)
            
            # Update user
            updates = {"password_hash": hashed_password}
            
            # Also verify user if they weren't verified (recovering account implies ownership)
            # Fetch user first to check status
            # existing = await self.get_user_by_id(UUID(user_id))
            # if existing and not existing.is_verified:
            #     updates["is_verified"] = True
            
            self.db.table("users").update(updates).eq("id", user_id).execute()
            
            # Invalidate cache
            # We need email for cache key, easiest to just clear by ID if we could, 
            # but our cache is by email. Let's just create a method to clear cache by ID or skip it.
            # Ideally fetch user to get email.
            user = await self.get_user_by_id(UUID(user_id))
            if user:
                cache_key = f"user:email:{user.email}"
                _user_cache.pop(cache_key, None)
                
            return True
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="Reset link has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=400, detail="Invalid reset link")
        except Exception as e:
            print(f"Password reset error: {e}")
            raise HTTPException(status_code=500, detail="Failed to reset password")