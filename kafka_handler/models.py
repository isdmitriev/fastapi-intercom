from pydantic import BaseModel
from typing import Dict, Any


class KafkaConsumerConfig(BaseModel):
    topic: str
    key: str
    payload: Dict[str, Any]
    consumer_group: str
    bootstrap_servers: Any
