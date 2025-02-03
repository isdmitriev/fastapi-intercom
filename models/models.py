from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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
