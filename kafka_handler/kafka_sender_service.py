from abc import ABC, abstractmethod
from dependency_injector.wiring import inject
from kafka_handler.kafka_clients_service import KafkaClientsService
from aiokafka.errors import KafkaError
from dotenv import load_dotenv
import os
from typing import Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

load_dotenv()


class KafkaSender(ABC):
    @inject
    def __init__(self, clients_service: KafkaClientsService):
        self.clients_service = clients_service

    @abstractmethod
    async def send_message(self, topic: str, key: str, payload: Dict[str, Any]):
        pass

    @abstractmethod
    async def stop_producer(self):
        pass

    @abstractmethod
    async def start_producer(self):
        pass

    def get_producer_client(self, bootstrap_servers):
        return self.clients_service.get_producer_client(
            bootstrap_servers=bootstrap_servers
        )


class KafkaSenderService(KafkaSender):
    @inject
    def __init__(self, clients_service: KafkaClientsService):
        super().__init__(clients_service=clients_service)
        self.kafka_producer_client = self.get_producer_client(
            bootstrap_servers=os.getenv("KAFKA_BROKER_URI")
        )
        self.produces_started = False

    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(KafkaError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def send_message(self, topic: str, key: str, payload: Dict[str, Any]):
        await self.start_producer()
        await self.kafka_producer_client.send(topic=topic, key=key, value=payload)

    async def stop_producer(self):
        await self.kafka_producer_client.stop()
        self.produces_started = False

    async def start_producer(self):
        if self.produces_started == False:
            await self.kafka_producer_client.start()
            self.produces_started = True
