import datetime
from tasks import mongodb_task, mongodb_task_async
from services.intercom_api_service import IntercomAPIService
from typing import Dict
import pytest
import asyncio
from services.openai_api_service import OpenAIService
from di.di_container import Container
from services.redis_cache_service import RedisService, MessagesCache
from services.openai_translator_service import OpenAITranslatorService

CLIENT: IntercomAPIService = IntercomAPIService()
from services.mongodb_service import MongodbService
from models.models import MessageTranslated, User
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
#     conversation_id: str = "6"
#     note: str = "note from Isdmitriev2@gmail.com"
#     result = CLIENT.add_admin_note_to_conversation(
#         conversation_id=conversation_id, note=note, admin_id=admin_id
#     )
#     assert result[0] == 200
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

# def test_openai_detect_language():
#     hindi_message: str = 'मैं हिंदी बोलता हूँ'
#     result: str = OpenAIService().detect_language(hindi_message)
#
#     assert result == 'hi'
#
#
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
    client: OpenAITranslatorService = OpenAITranslatorService()
    result = await client.detect_language_async(
        'Yaar mera khata freeze ho gaya hai, kitna gas bacha hai balance mein check karo please')

    result_hindi = await client.translate_message_from_english_to_hindi_async('hello')
    print(result_hindi)
    hindi = await client.detect_language_async(result_hindi)
    assert result == 'Hinglish'
    assert hindi == 'Hindi'


@pytest.mark.asyncio
async def test_analyze_message():
    open_ai_client = OpenAIService()
    message: UserMessage = await open_ai_client.analyze_message_with_correction(
        message="Yaar mera khata freeze ho gaya hai, kitna gas bacha hai balance mein check karo please"

    )
    print(message)
    assert isinstance(message, UserMessage)
