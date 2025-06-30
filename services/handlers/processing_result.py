from models.custom_exceptions import APPException

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any, Dict


class ProcessingResult(BaseModel):
    is_success: bool
    event_type: str
    execution_time: float | None

    timestamp: Optional[datetime] = datetime.utcnow().isoformat()
