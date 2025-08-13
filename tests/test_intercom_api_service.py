import datetime
from tasks import mongodb_task, mongodb_task_async
from services.intercom_api_service import IntercomAPIService
from typing import Dict, List
import pytest
from unittest.mock import AsyncMock
import asyncio
from services.openai_api_service import OpenAIService
from services.es_service import ESService
from di.di_container import Container
from services.redis_cache_service import RedisService, MessagesCache
from services.openai_translator_service import OpenAITranslatorService
import traceback
from services.http_service import IntercomAPIServiceV2
from models.custom_exceptions import APPException
import time
from models.custom_exceptions import APPException
from services.mongodb_service import MongodbService
from services.handlers.common import MessageAnalysConfig
from models.models import ConversationMessages, ConversationMessage, UserMessage


# @pytest.mark.asyncio
# async def test_mongo_db_service():
#     client = MongodbService()
#     await client.add_document_to_collection(
#         "intercom_app", "event_logs", {"name": "ilya"}
#     )


# @pytest.mark.asyncio
# async def test_get_conversation():
#     id: str = '46'
#     response = await IntercomAPIService().get_conversation_parts_by_id_async(id)
#     assert response[0] == 200
#     await MongodbService().add_document_to_collection('intercom_app', 'conversation_parts', response[1])


# @pytest.mark.asyncio
# async def test_detect_language_async():
#     message: str = 'শুভ দিন'
#     result = await OpenAIService().detect_language_async(message)
#     assert result == 'bn'


@pytest.mark.asyncio
async def test_openai_detect_language():
    start_time = time.perf_counter()
    hindi_message: str = "मैं हिंदी बोलता हूँ"
    result: str = await OpenAITranslatorService().detect_language_async_v2(
        message=hindi_message
    )
    print(time.perf_counter() - start_time)

    assert result == "Hindi"


# def test_openai_service_translate_to_hindi():
#     hindi_message: str = 'मैं हिंदी बोलता हूँ'
#     result: str = OpenAIService().translate_message_from_hindi_to_english(hindi_message)
#     assert isinstance(result, str)
#
#
# def test_openai_service_translate_to_hindi(message: str):
#     english_message: str = 'I speak english'
#     result: str = OpenAIService().translate_message_from_english_to_hindi(english_message)
#
#     assert isinstance(result, str)


# @pytest.mark.asyncio
# async def test_add_translations():
#     user: User = User(type="user", email="user@mail.com", id="id")
#     translation = MessageTranslated(
#         conversation_id="1235rte34",
#         time=datetime.datetime.now(),
#         message="hello",
#         language="en",
#         translated_to="hi",
#         translated_message="hello",
#         user=user,
#     )
#     await MongodbService().add_message_translated(translation)


# def test_celery():
#     mongodb_task.apply_async(args=["hello"], queue="celery")


# def test_celery_async():
#     user: User = User(type="user", email="user@mail.com", id="id")
#     translation = MessageTranslated(
#         conversation_id="1235rte34",
#         time=datetime.datetime.now(),
#         message="hello from celery app",
#         language="en",
#         translated_to="hi",
#         translated_message="hello",
#         user=user,
#     )
#
#     mongodb_task_async.apply_async(args=[translation.dict()], queue="celery")
# def test_redis():
#     redis_client:RedisService = Container().redis_service()
#     assert redis_client.set_key('1234',1)==True


# def test_conversation_messages():
#     messages_cache: MessagesCache = MessagesCache()
#     user = User(id="123", name="John Doe", type='user', email='my@gmail.com')
#     message = ConversationMessage(
#         conversation_id="conv_1",
#         time=datetime.datetime.now(),
#         message="Привет!",
#         user=user,
#         language="en",
#         message_type="text"
#     )
#
#     conversations = ConversationMessages(messages=[message])
#     json_string = conversations.model_dump_json()
#     assert isinstance(json_string, str)
#     messages: ConversationMessages = ConversationMessages.model_validate_json(json_string)
#     assert isinstance(messages, ConversationMessages)
#     messages_cache.set_conversation_messages('12345', messages)
#
#     list_messages: ConversationMessages = messages_cache.get_conversation_messages(conversation_id='12345')
#     assert isinstance(list_messages, ConversationMessages)


@pytest.mark.asyncio
async def test_translator_service():
    start_time = time.perf_counter()
    client: OpenAITranslatorService = OpenAITranslatorService()
    result = await client.translate_message_from_english_to_hindi_async()

    print(result)
    print(time.perf_counter() - start_time)


@pytest.fixture
def intercom_client():
    return IntercomAPIService()


@pytest.fixture
def mocked_open_ai_service():
    messages_cache: MessagesCache = MessagesCache()
    open_ai_service: OpenAIService = OpenAIService(
        messages_cache_service=messages_cache
    )
    open_ai_service.get_chat_history = AsyncMock(
        return_value=[{"role": "user", "content": "good day!"}]
    )
    return open_ai_service


@pytest.mark.asyncio
async def test_open_ai_service(mocked_open_ai_service):
    assert isinstance(mocked_open_ai_service, OpenAIService)
    history = await mocked_open_ai_service.get_chat_history(conversation_id="1")
    assert isinstance(history, List)
    analys_config: MessageAnalysConfig = MessageAnalysConfig()


@pytest.mark.asyncio
async def test_intercom_api_service(intercom_client):
    admin_id: str = "8736174"
    conversation_id: str = "215470301462007"
    note: str = "good day!"

    status, data = await intercom_client.add_admin_note_to_conversation_async(
        conversation_id=conversation_id, admin_id=admin_id, note=note
    )
    assert status == 200
    assert isinstance(data, Dict)


@pytest.mark.asyncio
async def test_custom_decorator_intercom_api(intercom_client):
    admin_id: str = "8736174"
    conversation_id: str = "215470301462007"
    note: str = "good day!"

    with pytest.raises(APPException) as ex1:
        await intercom_client.add_admin_note_to_conversation_async(
            conversation_id=conversation_id, admin_id=admin_id, note=note
        )
    with pytest.raises(APPException) as ex2:
        await intercom_client.add_admin_message_to_conversation_async(
            conversation_id=conversation_id, admin_id=admin_id, message=note
        )
    exception1 = ex1.value
    assert isinstance(exception1, APPException)
    assert exception1.params.get("conversation_id", "") == conversation_id
    exception2 = ex2.value
    assert isinstance(exception2, APPException)
    assert exception2.params.get("conversation_id", "") == conversation_id
