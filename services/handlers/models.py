from pydantic import BaseModel
from typing import Optional


class MessageAnalysResponse(BaseModel):
    note_for_admin: str
    chat_context_analys: Optional[str] = None


class MessageAnalysConfig(BaseModel):
    message: str
    chat_context: Optional[str] = None
    conversation_id: Optional[str] = None
    model: str
    type: str
