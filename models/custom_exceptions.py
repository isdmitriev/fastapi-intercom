from datetime import datetime
from typing import Optional, List, Any, Dict


class IntercomAPIException(Exception):
    def __init__(
            self,
            message,
            trace_stack: str,
            type: str,
            time: datetime,
            admin_id: str,
            user_id: str,
            conversation_id: str,
            message_text: str,
            event_type: str,
            method_name: str
    ):
        super().__init__(message)
        self.trace_stack = trace_stack
        self.type = type
        self.time = time
        self.admin_id = admin_id
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.message_text = message_text
        self.event_type = event_type
        self.method_name = method_name
