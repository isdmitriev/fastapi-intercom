from kafka_handler.kafka_clients_service import KafkaClientsService
from di.di_container import Container
from kafka_handler.kafka_sender_service import KafkaSender
from aiokafka import AIOKafkaProducer
import pytest


@pytest.mark.asyncio
async def test_clients_service():
    client: KafkaClientsService = Container.kafka_clients_service()
    assert isinstance(client, KafkaClientsService)
    producer: AIOKafkaProducer = await client.get_producer_client(bootstrap_servers='localhost:9092')

    assert isinstance(producer, AIOKafkaProducer)
@pytest.mark.asyncio
async def test_send_message():
    sender:KafkaSender=Container.kafka_sender_service()
    assert isinstance(sender,KafkaSender)
    await sender.send_message(topic='intercom_test',key='123',payload={'message':'test2'})


