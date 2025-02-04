from typing import Dict
from services.mongodb_service import MongodbService
from services.openai_api_service import OpenAIService
from bs4 import BeautifulSoup
from services.intercom_api_service import IntercomAPIService
from models.models import User, MessageTranslated
import datetime


class WebHookProcessor:

    def __init__(self):
        self.mongo_db_service = MongodbService()
        self.openai_service = OpenAIService()
        self.intercom_service = IntercomAPIService()

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
        message_language_code: str = self.openai_service.detect_language(clean_message)
        if message_language_code == "hi":
            message_for_admin: str = (
                self.openai_service.translate_message_from_hindi_to_english(
                    clean_message
                )
            )
            response = self.intercom_service.add_admin_note_to_conversation(
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
                conversation_id=conversation_id
            )
            await self.mongo_db_service.add_message_translated(translation)

            return
        else:
            return

    async def handle_conversation_admin_replied(self, data: Dict):
        print("conversation.admin.replied")

    async def handle_conversation_admin_noted(self, data: Dict):
        print("conversation.admin.noted")

    async def handle_conversation_admin_assigned(self, data: Dict):
        print("conversation.admin.assigned")
