from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any, Dict


class HTTPResponseData(BaseModel):
    is_success: bool
    status_code: str
    status_text: str
    data: Optional[Dict[str, Any]] | None = None
    exception_message: Optional[str | None] = None


class User(BaseModel):
    type: str
    email: str
    name: Optional[str] = None
    id: str


class MessageTranslated(BaseModel):
    conversation_id: str
    time: datetime
    message: str
    language: str
    translated_to: str
    translated_message: str
    user: User


class ConversationMessage(BaseModel):
    conversation_id: str
    time: datetime
    message: str
    user: User
    language: str
    message_type: str


class ConversationMessages(BaseModel):
    messages: List[ConversationMessage] = []
