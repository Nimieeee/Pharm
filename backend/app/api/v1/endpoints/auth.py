"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import shutil
from uuid import uuid4
from typing import Optional
import pathlib
from supabase import Client

from app.core.database import get_db
from app.services.auth import AuthService
from app.models.auth import Token, LoginRequest, RefreshTokenRequest, VerifyEmailRequest
from app.models.user import User, UserCreate, UserUpdate
from supabase import create_client, Client

router = APIRouter()
security = HTTPBearer()


def get_auth_service(db: Client = Depends(get_db)) -> AuthService:
    """Get authentication service"""
    return AuthService(db)


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user
    
    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **first_name**: Optional first name
    - **last_name**: Optional last name
    """
    try:
        user = await auth_service.register_user(user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email and password
    
    Returns JWT access token and refresh token
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            login_data.email, 
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Update last_login timestamp
        try:
            from app.core.database import get_db
            from datetime import datetime
            db = get_db()
            db.table("users").update({
                "last_login": datetime.utcnow().isoformat()
            }).eq("id", str(user.id)).execute()
        except Exception as e:
            print(f"⚠️ Failed to update last_login: {e}")
        
        # Create tokens
        tokens = await auth_service.create_tokens(user)
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token
    """
    try:
        tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_email(
    verify_data: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify email address with code
    """
    try:
        success = await auth_service.verify_user_email(verify_data.email, verify_data.code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
            
        return {"message": "Email verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )

@router.get("/me", response_model=User)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current user profile
    
    Requires valid JWT token in Authorization header
    """
    try:
        # Verify token
        token_data = auth_service.verify_token(credentials.credentials)
        
        # Get user
        user = await auth_service.get_user_by_email(token_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.post("/logout")
async def logout():
    """
    Logout user
    
    Note: JWT tokens are stateless, so logout is handled client-side
    by removing tokens from storage
    """
    return {"message": "Successfully logged out"}


# Dependency to get current user
async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Dependency to get current authenticated user"""
    try:
        # Verify token
        token_data = auth_service.verify_token(credentials.credentials)
        
        # Get user
        user = await auth_service.get_user_by_email(token_data.email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


# Dependency to get current admin user
async def get_current_admin_user(
    current_user: User = Depends(get_current_user_dependency)
) -> User:
    """Dependency to get current authenticated admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.put("/profile", response_model=User)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user_dependency),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update current user profile
    """
    # Only allow updating names and avatar_url via this endpoint
    # Email updates might require verification, handled separately
    update_data = user_update.dict(exclude_unset=True)
    
    # Don't allow updating sensitive fields here
    update_data.pop("is_admin", None)
    update_data.pop("is_active", None)
    
    updated_user = await auth_service.update_user(current_user.id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    return updated_user


@router.post("/profile/avatar", response_model=User)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_dependency),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Upload and set user avatar
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create avatar filename
    extension = os.path.splitext(file.filename)[1]
    if not extension:
        extension = ".png"
    
    avatar_name = f"{current_user.id}_{uuid4().hex[:8]}{extension}"
    
    try:
        # Upload to Supabase Storage
        file_content = await file.read()
        res = auth_service.db.storage.from_("avatars").upload(
            path=avatar_name,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Construct Public URL
        # Retrieve SUPABASE_URL from settings or env
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
             # Fallback to settings if env not reliable in this context?
             # But settings is imported from app.core.config
             from app.core.config import settings
             supabase_url = settings.SUPABASE_URL
             
        # Remove trailing slash if present
        supabase_url = supabase_url.rstrip("/")
        avatar_url = f"{supabase_url}/storage/v1/object/public/avatars/{avatar_name}"
        
    except Exception as e:
        print(f"❌ Error uploading avatar to Supabase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not upload image: {str(e)}"
        )
    
    # Update user avatar_url
    updated_user = await auth_service.update_user(current_user.id, {"avatar_url": avatar_url})
    
    if not updated_user:
        print(f"⚠️ Could not persist avatar_url to DB for user {current_user.id}")
        updated_user = current_user.model_copy(update={"avatar_url": avatar_url})
    
    return updated_user


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user: User = Depends(get_current_user_dependency),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Delete current user account permanently
    """
    success = await auth_service.delete_user(current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )