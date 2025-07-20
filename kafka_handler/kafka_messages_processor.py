from abc import ABC, abstractmethod
from dependency_injector.wiring import inject
from kafka_clients_service import KafkaClientsService
from services.handlers.messages_processor import MessagesProcessor
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import os
from dotenv import load_dotenv
from aiokafka.errors import KafkaError
from models.custom_exceptions import APPException
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from typing import Optional

load_dotenv()


class KafkaProcessor(ABC):
    @inject
    def __init__(self, clients_service: KafkaClientsService, messages_processor: MessagesProcessor):
        self.clients_service = clients_service
        self.messages_processor = messages_processor

    @abstractmethod
    async def consume_messages(self):
        pass


class KafkaService(KafkaProcessor):
    @inject
    def __init__(self, clients_service: KafkaClientsService, messages_processor: MessagesProcessor):
        super().__init__(clients_service=clients_service, messages_processor=messages_processor)
        self.consumer_client: Optional[AIOKafkaConsumer] = None

    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(KafkaError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def consume_messages(self):
        await self.init_client()
        try:

            async for message in self.consumer_client:
                payload = message.value
                await self.messages_processor.process_message(payload=payload)
        except(APPException, KafkaError) as error:
            pass
        except Exception as er:
            pass
        finally:
            pass

    async def init_client(self):
        self.consumer_client = await self.clients_service.get_consumer_client(
            bootstrap_servers=os.getenv('KAFKA_BROKER_URI'), topic=os.getenv('KAFKA_TOPIC'),
            group=os.getenv('KAFKA_GROUP'))
        await self.consumer_client.start()

    async def stop_client(self):
        await self.consumer_client.stop()
