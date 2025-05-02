import asyncio
from aiokafka import AIOKafkaProducer
from typing import Dict
import json


class KafkaProducerService:
    def __init__(self):
        pass

    async def send_message_async(self,key:str, payload: Dict):
        producer = AIOKafkaProducer(
            bootstrap_servers="localhost:9092",
            key_serializer=lambda k: k.encode("utf-8"),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await producer.start()
        await producer.send_and_wait(topic='intercom',key=key, value=payload)
        await producer.stop()
