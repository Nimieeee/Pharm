"""
Conversation data models and schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, field_validator


class ConversationBase(BaseModel):
    """Base conversation model"""
    title: str


class ConversationCreate(ConversationBase):
    """Conversation creation model"""
    pass


class ConversationUpdate(BaseModel):
    """Conversation update model"""
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


class ConversationInDB(ConversationBase):
    """Conversation model as stored in database"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    is_archived: bool = False
    
    class Config:
        from_attributes = True


class Conversation(ConversationBase):
    """Conversation model for API responses"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    is_archived: bool = False
    message_count: int = 0
    document_count: int = 0
    last_activity: Optional[datetime] = None
    title_translations: Optional[Dict[str, str]] = None  # Pre-generated title translations
    
    class Config:
        from_attributes = True

    @field_validator('title_translations', mode='before')
    @classmethod
    def parse_title_translations(cls, v: Any) -> Optional[Dict[str, str]]:
        if v is None:
            return None
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v


class MessageBase(BaseModel):
    """Base message model"""
    role: str  # 'user' or 'assistant'
    content: str
    metadata: Dict[str, Any] = {}
    translations: Optional[Dict[str, str]] = None  # Pre-generated translations {lang_code: text}

    @field_validator('translations', mode='before')
    @classmethod
    def parse_translations(cls, v: Any) -> Optional[Dict[str, str]]:
        if v is None:
            return None
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v


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
        from_attributes = True


class Message(MessageBase):
    """Message model for API responses"""
    id: UUID
    conversation_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationWithMessages(Conversation):
    """Conversation with messages included"""
    messages: List[Message] = []