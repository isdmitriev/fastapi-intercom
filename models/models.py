from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any, Dict
from models.custom_exceptions import APPException


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


class ConversationContext(BaseModel):
    last_user_message: str
    current_context_analys: str


class ConversationMessage(BaseModel):
    conversation_id: str
    time: datetime
    message: str
    user: User
    language: str
    message_type: str
    translated_en: Optional[str] = None


class ConversationMessages(BaseModel):
    messages: List[ConversationMessage] = []


class UserMessage(BaseModel):
    status: str
    original_text: str
    translated_text: str
    note: str | None
    possible_interpretations: List[str] = []
    corrected_text: str
    context_analysis: str
    language: Optional[str] = None


class RequestInfo(BaseModel):
    status: str
    execution_time: float | None
    event_type: str
    exception: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = datetime.utcnow().isoformat()
