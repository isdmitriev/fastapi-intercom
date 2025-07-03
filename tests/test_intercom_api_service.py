import datetime
from tasks import mongodb_task, mongodb_task_async
from services.intercom_api_service import IntercomAPIService
from typing import Dict
import pytest
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


CLIENT: IntercomAPIService = IntercomAPIService()
from services.mongodb_service import MongodbService
from models.models import MessageTranslated, User, RequestInfo
from models.models import ConversationMessages, ConversationMessage, UserMessage


# @pytest.mark.asyncio
# async def test_mongo_db_service():
#     client = MongodbService()
#     await client.add_document_to_collection(
#         "intercom_app", "event_logs", {"name": "ilya"}
#     )


def test_get_admins():
    result = CLIENT.get_all_admins()
    status_code, data = result
    print(data)

    assert status_code == 200


# def test_add_admin_message_to_conversation():
#     admin_id: str = "8028082"
#     conversation_id: str = "6"
#     message: str = "i am Isdmitriev2@gmail.com"
#
#     result = CLIENT.add_admin_message_to_conversation(
#         admin_id=admin_id, conversation_id=conversation_id, message=message
#     )
#     assert result[0] == 200


# def test_add_admin_note_to_conversation():
#     admin_id: str = "8028082"
#     conversation_id: str = "0"
#     note: str = "note from Isdmitriev2@gmail.com"
#     print(note)
#
#     result = CLIENT.add_admin_note_to_conversation(
#             conversation_id=conversation_id, note=note, admin_id=admin_id
#     )


# @pytest.mark.asyncio
# async def test_process():
#     user_id: str = "6798a0c79645a8b3711b89d3"
#     admin_id: str = "8028082"
#     create_conversation_response: str = CLIENT.create_conversation(
#         user_id=user_id, message="good day!"
#     )
#     status = create_conversation_response[0]
#     json_data = create_conversation_response[1]
#     assert status == 200
#     new_conversatin_id: str = json_data.get("conversation_id", "")
#     attach_admin_to_conversation_response = CLIENT.attach_admin_to_conversation(
#         conversation_id=new_conversatin_id, admin_id=admin_id
#     )
#     assert attach_admin_to_conversation_response[0] == 200
#
#     test_user_replied_response = await CLIENT.add_user_replied_to_conversation(
#         conversation_id=new_conversatin_id, user_id=user_id, message='अच्छा दिन'
#     )
#     assert test_user_replied_response[0] == 200
#     test_add_admin_message_to_conversation_response = (
#         CLIENT.add_admin_message_to_conversation(
#             conversation_id=new_conversatin_id,
#             admin_id=admin_id,
#             message="admin message",
#         )
#     )
#     assert test_add_admin_message_to_conversation_response[0] == 200
#     add_admin_note_to_conversation_response = CLIENT.add_admin_note_to_conversation(
#         conversation_id=new_conversatin_id, note="note", admin_id=admin_id
#     )
#     assert add_admin_note_to_conversation_response[0] == 200

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
def test_conversation_language():
    try:
        redis_cache: MessagesCache = MessagesCache()
        redis_cache.set_conversation_language(
            conversation_id="155", language="Hinglish"
        )
        language: str = redis_cache.get_conversation_language(conversation_id="155")
        assert language == "Hinglish"
    except Exception as e:
        print(type(e).__module__ + type(e).__name__)
        print(str(e))


@pytest.mark.asyncio
async def test_translator_service():
    start_time = time.perf_counter()
    client: OpenAITranslatorService = OpenAITranslatorService()
    result = await client.translate_message_from_english_to_hindi_async()

    print(result)
    print(time.perf_counter() - start_time)


@pytest.mark.asyncio
async def test_openai():
    conv_id = "conv:215468885032326"

    client: OpenAIService = Container.open_ai_service()
    start_time = time.perf_counter()
    message: str = await client.analyze_message_with_correction_v4(
        message="namaste!", analys=""
    )
    assert isinstance(message, UserMessage)

    # assert isinstance(message, UserMessage)
    print(time.perf_counter() - start_time)
    print(message)


# def test_intercom_api():
#     client: IntercomAPIService = IntercomAPIService()
#     response = client.get_all_admins()
#     print(response[1])

# @pytest.mark.asyncio
# async def test_analyze_message():
#     open_ai_client = OpenAIService()
#     await open_ai_client.analyze_message_with_correction_async_v2(
#         message="Bhai site par login nahi ho pa raha hai, mera engine start hi nahi ho raha, password dalte hi petrol khatam ho jata hai"
#     )


# @pytest.mark.asyncio
# async def test_intercom_client_v2():
#     admin_id: str = "8028082"
#     client: IntercomAPIServiceV2 = IntercomAPIServiceV2()
#     with pytest.raises(APPException) as app_exception:
#         start = time.perf_counter()
#         result = await client.add_admin_note_to_conversation_async(
#             conversation_id="170", admin_id=admin_id, note="good day!"
#         )
#         end = time.perf_counter()
#         print(f"Время выполнения: {end - start:.6f} seconds")


# def test_es_service():
#     client: ESService = ESService()
#     # client.create_index('requests')
#     exception: APPException = APPException(
#         message="error",
#         event_type="conversation.admin.noted",
#         ex_class="class",
#         params={},
#     )
#     request_info: RequestInfo = RequestInfo(
#         exception=exception.__dict__,
#         status="error",
#         execution_time=None,
#         event_type="conversation.admin.noted",
#     )
#     res = client.add_document(index_name="requests", document=request_info.dict())
#     print(res)


# @pytest.mark.asyncio
# async def test_analyze_message_v3():
#     conversation_id: str = "conv:199"
#     client = OpenAIService()
#     result: UserMessage = await client.analyze_message_with_correction_v3(
#         message="namaste",
#         conversation_id=conversation_id
#     )
#     print(result)
#     print(result.context_analysis)
#     assert isinstance(result, UserMessage)
#
# @pytest.mark.asyncio
# async def test_analyze_message_claude():
#     conversation_id: str = "conv:199"
#     client =ClaudeService()
#     user_message:UserMessage=await client.analyze_message_with_correction(message='Meri button abhi bhi active nahi hai.',conversation_id=conversation_id)
#     print(user_message)
#     assert isinstance(user_message,UserMessage)
