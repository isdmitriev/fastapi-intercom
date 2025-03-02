from datetime import datetime
from typing import Optional, List, Any, Dict


class APPException(Exception):
    def __init__(self, message, event_type: str, ex_class: str, params: Dict):
        super().__init__(message)
        self.event_type = event_type
        self.ex_class = ex_class
        self.params = params
