"""
Support request data models
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, validator


class SupportRequestBase(BaseModel):
    """Base support request model"""
    email: EmailStr
    subject: str
    message: str
    
    @validator('subject')
    def validate_subject(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Subject must be at least 5 characters long')
        if len(v) > 500:
            raise ValueError('Subject must be less than 500 characters')
        return v.strip()
    
    @validator('message')
    def validate_message(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters long')
        if len(v) > 5000:
            raise ValueError('Message must be less than 5000 characters')
        return v.strip()


class SupportRequestCreate(SupportRequestBase):
    """Support request creation model"""
    pass


class SupportRequestUpdate(BaseModel):
    """Support request update model (admin only)"""
    status: Optional[str] = None
    admin_response: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['open', 'in_progress', 'resolved', 'closed']:
            raise ValueError('Invalid status')
        return v


class SupportRequestInDB(SupportRequestBase):
    """Support request model as stored in database"""
    id: UUID
    user_id: Optional[UUID] = None
    status: str = 'open'
    admin_response: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class SupportRequest(SupportRequestBase):
    """Support request model for API responses"""
    id: UUID
    user_id: Optional[UUID] = None
    status: str = 'open'
    admin_response: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class SupportRequestResponse(BaseModel):
    """Admin response to support request"""
    request_id: UUID
    response: str
    status: str = 'resolved'
    
    @validator('response')
    def validate_response(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Response must be at least 10 characters long')
        return v.strip()
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['in_progress', 'resolved', 'closed']:
            raise ValueError('Invalid status for response')
        return v