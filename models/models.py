from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


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
