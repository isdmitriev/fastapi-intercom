from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from abc import ABC, abstractmethod

import json


class ClientsServiceBase(ABC):

    def __init__(self):
        pass

    @abstractmethod
    async def get_producer_client(self, bootstrap_servers) -> AIOKafkaProducer:
        pass

    @abstractmethod
    async def get_consumer_client(
        self, bootstrap_servers: str, topic: str, group: str
    ) -> AIOKafkaConsumer:
        pass


class KafkaClientsService(ClientsServiceBase):
    async def get_producer_client(self, bootstrap_servers) -> AIOKafkaProducer:
        producer_client: AIOKafkaProducer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            key_serializer=lambda k: k.encode("utf-8"),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        return producer_client

    async def get_consumer_client(
        self, bootstrap_servers: str, topic: str, group: str
    ) -> AIOKafkaConsumer:
        consumer_client: AIOKafkaConsumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group,
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        return consumer_client
