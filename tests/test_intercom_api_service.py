import datetime

from services.intercom_api_service import IntercomAPIService
from typing import Dict
import pytest
import asyncio
from services.openai_api_service import OpenAIService

CLIENT: IntercomAPIService = IntercomAPIService()
from services.mongodb_service import MongodbService
from models.models import MessageTranslated, User


@pytest.mark.asyncio
async def test_mongo_db_service():
    client = MongodbService()
    await client.add_document_to_collection(
        "intercom_app", "event_logs", {"name": "ilya"}
    )


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
#         conversation_id=new_conversatin_id, user_id=user_id, message="reply_from_user"
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


def test_openai_detect_language():
    hindi_message: str = 'मैं हिंदी बोलता हूँ'
    result: str = OpenAIService().detect_language(hindi_message)

    assert result == 'hi'
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
#     user: User = User(type='user', email='user@mail.com', id='id')
#     translation = MessageTranslated(
#         conversation_id='1235rte34',
#         time=datetime.datetime.now(),
#         message='hello',
#         language='en',
#         translated_to='hi',
#         translated_message='hello',
#         user=user
#     )
#     await MongodbService().add_message_translated(translation)
