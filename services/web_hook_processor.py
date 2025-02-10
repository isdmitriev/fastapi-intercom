from typing import Dict
from services.mongodb_service import MongodbService
from services.openai_api_service import OpenAIService
from bs4 import BeautifulSoup
from services.intercom_api_service import IntercomAPIService
from models.models import User, MessageTranslated
from tasks import mongodb_task_async, translate_message_for_admin_bengali
import datetime
from services.conversation_parts_service import ConversationPartsService


class WebHookProcessor:

    def __init__(self):
        self.mongo_db_service = MongodbService()
        self.openai_service = OpenAIService()
        self.intercom_service = IntercomAPIService()
        self.conversation_parts_service = ConversationPartsService()

    async def process_message(self, topic: str, message: Dict):

        if topic == "conversation.user.created":
            await self.handle_conversation_user_created(data=message)
            return

        elif topic == "conversation.user.replied":
            await self.handle_conversation_user_replied(data=message)
            return

        elif topic == "conversation.admin.replied":
            await self.handle_conversation_admin_replied(data=message)
            return

        elif topic == "conversation.admin.noted":
            await self.handle_conversation_admin_noted(data=message)
            return

        elif topic == "conversation.admin.assigned":
            await self.handle_conversation_admin_assigned(data=message)
            return
        else:
            return

    async def handle_conversation_user_created(self, data: Dict):
        conversation_id: str = data.get("data", {}).get("item", {}).get("id", "")
        self.intercom_service.attach_admin_to_conversation(
            conversation_id=conversation_id, admin_id=8028082
        )
        user_data: Dict = data.get("data", {}).get("item", {}).get("source", {})
        message: str = user_data.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        user_id: str = data.get("author", {}).get("id", "")
        user_email: str = data.get("author", {}).get("email", "")

        message_language_code: str = await self.openai_service.detect_language_async(
            clean_message
        )
        if message_language_code == "hi":
            note_for_admin: str = (
                await self.openai_service.translate_message_from_hindi_to_english_async(
                    clean_message
                )
            )
            response = await self.intercom_service.add_admin_note_to_conversation_async(
                note=note_for_admin, admin_id=8024055, conversation_id=conversation_id
            )
        else:
            return

        print("conversation.user.created")

    async def handle_conversation_user_replied(self, data: Dict):
        user_reply: Dict = data["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = user_reply.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        user_email: str = user_reply.get("author", {}).get("email", "")
        user_id: str = user_reply.get("author", {}).get("id", "")
        conversation_id: str = data["data"]["item"]["id"]
        print(f"{clean_message}:{user_email}:{user_id}")
        print("conversation.user.replied")
        message_language_code: str = await self.openai_service.detect_language_async(
            clean_message
        )
        if message_language_code == "hi":
            message_for_admin: str = (
                await self.openai_service.translate_message_from_hindi_to_english_async(
                    clean_message
                )
            )
            response = await self.intercom_service.add_admin_note_to_conversation_async(
                note=message_for_admin,
                admin_id="8028082",
                conversation_id=conversation_id,
            )
            user: User = User(type="user", id=user_id, email=user_email)
            translation: MessageTranslated = MessageTranslated(
                user=user,
                language=message_language_code,
                message=clean_message,
                translated_message=message_for_admin,
                translated_to="en",
                time=datetime.datetime.now(),
                conversation_id=conversation_id,
            )
            mongodb_task_async.apply_async(args=[translation.dict()], queue="mongo_db")

            return
        elif message_language_code == "bn":
            message_for_admin: str = (
                await self.openai_service.translate_message_from_bengali_to_english_async(
                    message=clean_message
                )
            )
            response = await self.intercom_service.add_admin_note_to_conversation_async(
                note=message_for_admin,
                conversation_id=conversation_id,
                admin_id="8024055",
            )
            user: User = User(type="user", id=user_id, email=user_email)
            translation: MessageTranslated = MessageTranslated(
                user=user,
                language=message_language_code,
                message=clean_message,
                translated_message=message_for_admin,
                translated_to="en",
                time=datetime.datetime.now(),
                conversation_id=conversation_id,
            )
            mongodb_task_async.apply_async(args=[translation.dict()], queue="mongo_db")

            # translate_message_for_admin_bengali.apply_async(
            #     kwargs={
            #         "message": clean_message,
            #         "admin_id": "8028082",
            #         "conversation_id": conversation_id,
            #     },
            #     queue="admin_notes",
            # )
            return

        else:
            return

    async def handle_conversation_admin_replied(self, data: Dict):

        print("conversation.admin.replied")

    async def handle_conversation_admin_noted(self, data: Dict):
        print("conversation.admin.noted")
        admin_translator_id: str = "8024055"
        admin_note: Dict = data["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = admin_note.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        print(clean_message)
        admin_id: str = admin_note.get("author", {}).get("id", "")
        print(admin_id)
        conversation_id: str = data["data"]["item"]["id"]
        print(conversation_id)
        if admin_id != admin_translator_id:
            await self.conversation_parts_service.handle_admin_note(
                conversation_id=conversation_id,
                admin_id=admin_id,
                admin_note=clean_message,
            )

        print("conversation.admin.noted")

    async def handle_conversation_admin_assigned(self, data: Dict):
        print("conversation.admin.assigned")
