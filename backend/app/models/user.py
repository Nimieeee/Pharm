"""
User data models and schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False


class UserCreate(UserBase):
    """User creation model"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """User model as stored in database"""
    id: UUID
    password_hash: str
    is_admin: bool = False
    is_verified: bool = False
    verification_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class User(UserBase):
    """User model for API responses"""
    id: UUID
    is_admin: bool = False
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """Extended user profile"""
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_admin: bool = False
    is_verified: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    conversation_count: int = 0
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True