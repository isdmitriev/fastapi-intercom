import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from di.di_container import Container
from services.web_hook_processor import WebHookProcessor


class KafkaConsumerService:
    def __init__(self):
        pass

    async def process_message(self):
        consumer = self.get_client()
        processor: WebHookProcessor = Container.web_hook_processor()
        await consumer.start()
        try:

            async for msg in consumer:
                topic: str = msg.value.get("topic", "")
                print(topic)
                await processor.process_message(topic=topic, message=msg.value)




        finally:
            await consumer.stop()

    def get_client(self):
        consumer: AIOKafkaConsumer = AIOKafkaConsumer(
            "intercom",
            group_id="test-group",
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True
        )
        return consumer


asyncio.run(KafkaConsumerService().process_message())
