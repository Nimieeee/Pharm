"""
Conversation data models and schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel


class ConversationBase(BaseModel):
    """Base conversation model"""
    title: str


class ConversationCreate(ConversationBase):
    """Conversation creation model"""
    pass


class ConversationUpdate(BaseModel):
    """Conversation update model"""
    title: Optional[str] = None


class ConversationInDB(ConversationBase):
    """Conversation model as stored in database"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class Conversation(ConversationBase):
    """Conversation model for API responses"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    document_count: int = 0
    last_activity: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class MessageBase(BaseModel):
    """Base message model"""
    role: str  # 'user' or 'assistant'
    content: str
    metadata: Dict[str, Any] = {}


class MessageCreate(MessageBase):
    """Message creation model"""
    conversation_id: UUID


class MessageInDB(MessageBase):
    """Message model as stored in database"""
    id: UUID
    conversation_id: UUID
    user_id: UUID
    created_at: datetime
    
    class Config:
        orm_mode = True


class Message(MessageBase):
    """Message model for API responses"""
    id: UUID
    conversation_id: UUID
    created_at: datetime
    
    class Config:
        orm_mode = True


class ConversationWithMessages(Conversation):
    """Conversation with messages included"""
    messages: List[Message] = []