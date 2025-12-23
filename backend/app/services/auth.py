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

# Cache user lookups for 60 seconds to avoid hitting DB on every request
_user_cache = TTLCache(maxsize=500, ttl=60)


class AuthService:
    """Authentication service"""
    
    def __init__(self, db: Client):
        self.db = db
    
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
            
            # Pre-warm the cache so first authenticated request is fast
            cache_key = f"user:email:{email}"
            _user_cache[cache_key] = User(**user_data)
            
            return user
            
        except Exception:
            return None
    
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
            
            # Store in cache
            _user_cache[cache_key] = user
            return user
            
        except Exception:
            return None
    
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