"""
Authentication data models
"""

from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    is_admin: bool = False


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str
    
    def validate_new_password(self):
        """Validate new password strength"""
        password = self.new_password
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in password):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in password):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            raise ValueError('Password must contain at least one digit')
        return password


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str