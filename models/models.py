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


class MessageAlternative(BaseModel):
    original: str
    english: str


class MessageError(BaseModel):
    original: str
    english: str
    suggested_correction_en: str
    suggested_correction_origin: str
    alternatives: List[MessageAlternative] = []


class UserMessage(BaseModel):
    corrected_message_origin: str
    corrected_message_en: str
    errors: List[MessageError] = []
    message_language: str
    status: str
    original_message:str
