from typing import Dict
from services.mongodb_service import MongodbService
from services.openai_api_service import OpenAIService
from bs4 import BeautifulSoup
from services.intercom_api_service import IntercomAPIService
from models.models import (
    User,
    UserMessage,
    MessageTranslated,
    ConversationMessage,
    ConversationMessages,
)
from tasks import mongodb_task_async, translate_message_for_admin_bengali
import datetime
from services.conversation_parts_service import ConversationPartsService
from services.redis_cache_service import MessagesCache
from services.openai_translator_service import OpenAITranslatorService
from typing import List


class WebHookProcessor:

    def __init__(
            self,
            mongo_db_service: MongodbService,
            openai_service: OpenAIService,
            intercom_service: IntercomAPIService,
            conversation_parts_service: ConversationPartsService,
            messages_cache_service: MessagesCache,
            translations_service: OpenAITranslatorService,
    ):
        self.mongo_db_service = mongo_db_service
        self.openai_service = openai_service
        self.intercom_service = intercom_service
        self.conversation_parts_service = conversation_parts_service
        self.messages_cache_service = messages_cache_service
        self.translations_service = translations_service

    async def process_message(self, topic: str, message: Dict):

        if topic == "conversation.user.created":
            await self.handle_conversation_user_created_v3(data=message)
            return

        elif topic == "conversation.user.replied":
            await self.handle_conversation_user_replied_v3(data=message)
            return

        elif topic == "conversation.admin.replied":
            await self.handle_conversation_admin_replied(data=message)
            return

        elif topic == "conversation.admin.noted":
            await self.handle_conversation_admin_noted_v3(data=message)
            return

        elif topic == "conversation.admin.assigned":
            await self.handle_conversation_admin_assigned(data=message)
            return
        elif topic == "conversation.admin.closed":
            await self.handle_conversation_admin_closed(data=message)
            return

        else:
            return

    async def handle_conversation_admin_closed(self, data: Dict):
        conversation_id: str = data.get("data", {}).get("item", {}).get("id", "")
        self.messages_cache_service.delete_conversation(conversation_id=conversation_id)

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
        elif message_language_code == "bn":
            note_for_admin: str = (
                await self.openai_service.translate_message_from_bengali_to_english_async(
                    message=clean_message
                )
            )
            response = await self.intercom_service.add_admin_note_to_conversation_async(
                note=note_for_admin, admin_id="8024055", conversation_id=conversation_id
            )

        else:
            return

        print("conversation.user.created")

    async def handle_conversation_user_created_v3(self, data: Dict):
        print("conversation.user.created")
        conversation_id: str = data.get("data", {}).get("item", {}).get("id", "")
        self.intercom_service.attach_admin_to_conversation(
            conversation_id=conversation_id, admin_id=8028082
        )
        user_data: Dict = data.get("data", {}).get("item", {}).get("source", {})
        message: str = user_data.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        user_id: str = data.get("author", {}).get("id", "")
        user_email: str = data.get("author", {}).get("email", "")
        user: User = User(id=user_id, email=user_email, type="user")
        admin_id = "8024055"
        message_language: str = (
            await self.translations_service.detect_language_async_v2(
                message=clean_message
            )
        )
        message: ConversationMessage = ConversationMessage(
            conversation_id=conversation_id,
            time=datetime.datetime.now(),
            message=clean_message,
            user=user,
            language=message_language,
            message_type="conversation.user.created",
        )
        messages: ConversationMessages = ConversationMessages(messages=[message])
        self.messages_cache_service.set_conversation_messages(
            conversation_id=conversation_id, messages=messages
        )

        if message_language in ["English", "Hindi", "Hinglish", "Bengali"]:
            analyzed_user_message: UserMessage = (
                await self.openai_service.analyze_message_with_correction(
                    message=clean_message
                )
            )
            original_message = analyzed_user_message.original_text
            corrected_message = analyzed_user_message.corrected_text
            translated_text = analyzed_user_message.translated_text

            if analyzed_user_message.status == "no_error":
                if message_language == "Hindi":
                    await self.send_admin_note_async(
                        conversation_id=conversation_id,
                        message=clean_message,
                        message_language=message_language,
                    )

                elif message_language == "Hinglish":
                    await self.send_admin_note_async(
                        conversation_id=conversation_id,
                        message=clean_message,
                        message_language=message_language,
                    )

                elif message_language == "Bengali":
                    await self.send_admin_note_async(
                        conversation_id=conversation_id,
                        message=clean_message,
                        message_language=message_language,
                    )

                else:
                    return

            elif analyzed_user_message.status == "error_fixed":
                if message_language == "Hindi":
                    await self.send_admin_note_async(
                        conversation_id=conversation_id,
                        message=corrected_message,
                        message_language=message_language,
                    )
                if message_language == "Hinglish":
                    await self.send_admin_note_async(
                        conversation_id=conversation_id,
                        message=corrected_message,
                        message_language=message_language,
                    )
                if message_language == "Bengali":
                    await self.send_admin_note_async(
                        conversation_id=conversation_id,
                        message=corrected_message,
                        message_language=message_language,
                    )
            elif analyzed_user_message.status == "uncertain":
                note: str = await self.create_admin_note(analyzed_user_message)

                await self.send_admin_note_async(
                    conversation_id=conversation_id,
                    message=note,
                    message_language="English",
                )

    async def send_admin_note_async(
            self, conversation_id: str, message: str, message_language
    ):
        admin_id: str = "8024055"
        if message_language == "Hindi":
            note_for_admin: str = (
                await self.translations_service.translate_message_from_hindi_to_english_async(
                    message=message
                )
            )
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                note=note_for_admin,
            )
            return
        elif message_language == "Hinglish":
            note_for_admin: str = (
                await self.translations_service.translate_message_from_hinglish_to_english_async(
                    message=message
                )
            )
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                note=note_for_admin,
            )
            return
        elif message_language == "Bengali":
            note_for_admin: str = (
                await self.translations_service.translate_message_from_bengali_to_english_async(
                    message=message
                )
            )
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                note=note_for_admin,
            )
            return
        elif message_language == "English":
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id, admin_id=admin_id, note=message
            )
            return
        else:
            return

    async def create_admin_note(self, message: UserMessage):
        note: str = "translated: " + message.translated_text + "\n" + message.note
        return note

    async def handle_conversation_user_created_v2(self, data: Dict):
        conversation_id: str = data.get("data", {}).get("item", {}).get("id", "")
        self.intercom_service.attach_admin_to_conversation(
            conversation_id=conversation_id, admin_id=8028082
        )
        user_data: Dict = data.get("data", {}).get("item", {}).get("source", {})
        message: str = user_data.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        user_id: str = data.get("author", {}).get("id", "")
        user_email: str = data.get("author", {}).get("email", "")

        user: User = User(id=user_id, email=user_email, type="user")

        message_language_code: str = await self.openai_service.detect_language_async(
            message=clean_message
        )
        message: ConversationMessage = ConversationMessage(
            conversation_id=conversation_id,
            time=datetime.datetime.now(),
            message=clean_message,
            user=user,
            language=message_language_code,
            message_type="conversation.user.created",
        )
        messages: ConversationMessages = ConversationMessages(messages=[message])
        self.messages_cache_service.set_conversation_messages(
            conversation_id=conversation_id, messages=messages
        )

        if message_language_code == "en":
            return

        elif message_language_code == "hi":
            note_for_admin: str = (
                await self.openai_service.translate_message_from_hindi_to_english_async(
                    message=clean_message
                )
            )
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id, admin_id="8024055", note=note_for_admin
            )
        elif message_language_code == "bn":
            note_for_admin: str = (
                await self.openai_service.translate_message_from_bengali_to_english_async(
                    message=clean_message
                )
            )
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id, admin_id="8024055", note=note_for_admin
            )
        else:
            return

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
                admin_id="8024055",
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
            # mongodb_task_async.apply_async(args=[translation.dict()], queue="mongo_db")

            return
        elif message_language_code == "bn" or message_language_code == "ben":
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
            # mongodb_task_async.apply_async(args=[translation.dict()], queue="mongo_db")

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

    async def handle_conversation_user_replied_v3(self, data: Dict):
        user_reply: Dict = data["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = user_reply.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        user_email: str = user_reply.get("author", {}).get("email", "")
        user_id: str = user_reply.get("author", {}).get("id", "")
        conversation_id: str = data["data"]["item"]["id"]
        message_language: str = (
            await self.translations_service.detect_language_async_v2(
                message=clean_message
            )
        )
        user: User = User(id=user_id, email=user_email, type="user")
        message: ConversationMessage = ConversationMessage(
            conversation_id=conversation_id,
            time=datetime.datetime.now(),
            message=clean_message,
            user=user,
            language=message_language,
            message_type="conversation.user.replied",
        )
        all_messages: ConversationMessages = (
            self.messages_cache_service.get_conversation_messages(
                conversation_id=conversation_id
            )
        )
        all_messages.messages.append(message)
        self.messages_cache_service.set_conversation_messages(
            conversation_id=conversation_id, messages=all_messages
        )

        if message_language in ["English", "Hindi", "Hinglish", "Bengali"]:
            analyzed_message: UserMessage = (
                await self.openai_service.analyze_message_with_correction(
                    message=clean_message
                )
            )
            if analyzed_message.status == "no_error":
                if message_language != "English":
                    await self.send_admin_note_async(
                        conversation_id=conversation_id,
                        message=clean_message,
                        message_language=message_language,
                    )
            if analyzed_message.status == "error_fixed":
                corrected_message: str = analyzed_message.corrected_text
                await self.send_admin_note_async(
                    conversation_id=conversation_id,
                    message=corrected_message,
                    message_language=message_language,
                )
            if analyzed_message.status == "uncertain":
                note: str = await self.create_admin_note(analyzed_message)
                await self.send_admin_note_async(
                    conversation_id=conversation_id,
                    message=note,
                    message_language="English",
                )
        return

    async def handle_conversation_user_replied_v2(self, data: Dict):
        user_reply: Dict = data["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = user_reply.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        user_email: str = user_reply.get("author", {}).get("email", "")
        user_id: str = user_reply.get("author", {}).get("id", "")
        conversation_id: str = data["data"]["item"]["id"]
        message_language_code: str = await self.openai_service.detect_language_async(
            clean_message
        )
        user: User = User(id=user_id, email=user_email, type="user")
        message: ConversationMessage = ConversationMessage(
            conversation_id=conversation_id,
            time=datetime.datetime.now(),
            message=clean_message,
            user=user,
            language=message_language_code,
            message_type="conversation.user.replied",
        )
        all_messages: ConversationMessages = (
            self.messages_cache_service.get_conversation_messages(
                conversation_id=conversation_id
            )
        )
        all_messages.messages.append(message)
        self.messages_cache_service.set_conversation_messages(
            conversation_id=conversation_id, messages=all_messages
        )
        if message_language_code == "en":
            return
        elif message_language_code == "bn" or message_language_code == "ben":
            note_for_admin: str = (
                await self.openai_service.translate_message_from_bengali_to_english_async(
                    message=clean_message
                )
            )
            await self.intercom_service.add_admin_note_to_conversation_async(
                note=note_for_admin, conversation_id=conversation_id, admin_id="8024055"
            )
            translation: MessageTranslated = MessageTranslated(
                user=user,
                language=message_language_code,
                message=clean_message,
                translated_message=note_for_admin,
                translated_to="en",
                time=datetime.datetime.now(),
                conversation_id=conversation_id,
            )
            mongodb_task_async.apply_async(args=[translation.dict()], queue="mongo_db")

        elif message_language_code == "hi":
            note_for_admin: str = (
                await self.openai_service.translate_message_from_hindi_to_english_async(
                    message=clean_message
                )
            )
            await self.intercom_service.add_admin_note_to_conversation_async(
                note=note_for_admin, conversation_id=conversation_id, admin_id="8024055"
            )

            translation: MessageTranslated = MessageTranslated(
                user=user,
                language=message_language_code,
                message=clean_message,
                translated_message=note_for_admin,
                translated_to="en",
                time=datetime.datetime.now(),
                conversation_id=conversation_id,
            )
            # mongodb_task_async.apply_async(args=[translation.dict()], queue="mongo_db")

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

    async def handle_conversation_admin_noted_v3(self, data: Dict):
        print("conversation.admin.noted")
        admin_translator_id: str = "8024055"
        admin_note: Dict = data["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = admin_note.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        admin_id: str = admin_note.get("author", {}).get("id", "")
        conversation_id: str = data["data"]["item"]["id"]
        if admin_id != admin_translator_id:
            user: User = User(id=admin_id, email="em@gmail.com", type="admin")
            print(user)
            message: ConversationMessage = ConversationMessage(
                conversation_id=conversation_id,
                time=datetime.datetime.now(),
                message=clean_message,
                user=user,
                language="English",
                message_type="conversation.admin.noted",
            )
            conversation_messages: ConversationMessages = (
                self.messages_cache_service.get_conversation_messages(
                    conversation_id=conversation_id
                )
            )
            all_messages: List[ConversationMessage] = list(
                reversed(conversation_messages.messages)
            )
            conversation_messages.messages.append(message)
            self.messages_cache_service.set_conversation_messages(
                conversation_id=conversation_id, messages=conversation_messages
            )
            for conv_message in all_messages:
                if conv_message.user.type == "user":
                    if conv_message.language == "Hinglish":
                        admin_reply_message: str = (
                            await self.translations_service.translate_message_from_english_to_hinglish_async_v2(
                                message=clean_message
                            )
                        )
                        await self.intercom_service.add_admin_message_to_conversation_async(
                            conversation_id=conversation_id,
                            admin_id=admin_id,
                            message=admin_reply_message,
                        )
                        return
                    elif conv_message.language == "Hindi":
                        admin_reply_message: str = (
                            await self.translations_service.translate_message_from_english_to_hindi_async(
                                message=clean_message
                            )
                        )
                        await self.intercom_service.add_admin_message_to_conversation_async(
                            conversation_id=conversation_id,
                            admin_id=admin_id,
                            message=admin_reply_message,
                        )
                        return
                    elif conv_message.language == "Bengali":
                        admin_reply_message: str = (
                            await self.translations_service.translate_message_from_english_to_bengali_async(
                                message=clean_message
                            )
                        )
                        await self.intercom_service.add_admin_message_to_conversation_async(
                            conversation_id=conversation_id,
                            admin_id=admin_id,
                            message=admin_reply_message,
                        )
                        return

                    elif conv_message.language == "English":
                        await self.intercom_service.add_admin_message_to_conversation_async(
                            conversation_id=conversation_id,
                            admin_id=admin_id,
                            message=clean_message,
                        )
                        return
                    else:
                        continue

    async def handle_conversation_admin_noted_v2(self, data: Dict):
        admin_translator_id: str = "8024055"
        admin_note: Dict = data["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = admin_note.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        admin_id: str = admin_note.get("author", {}).get("id", "")
        conversation_id: str = data["data"]["item"]["id"]
        if admin_id != admin_translator_id:
            user: User = User(id=admin_id, email="em@gmail.com", type="admin")
            message: ConversationMessage = ConversationMessage(
                conversation_id=conversation_id,
                time=datetime.datetime.now(),
                message=clean_message,
                user=user,
                language="en",
                message_type="conversation.admin.noted",
            )
            conversation_messages: ConversationMessages = (
                self.messages_cache_service.get_conversation_messages(
                    conversation_id=conversation_id
                )
            )
            all_messages: List[ConversationMessage] = list(
                reversed(conversation_messages.messages)
            )
            conversation_messages.messages.append(message)
            self.messages_cache_service.set_conversation_messages(
                conversation_id=conversation_id, messages=conversation_messages
            )
            for message in all_messages:
                if message.user.type == "user":
                    if message.language == "hi":
                        admin_reply_message: str = (
                            await self.openai_service.translate_message_from_english_to_hindi_async(
                                message=clean_message
                            )
                        )
                        await self.intercom_service.add_admin_message_to_conversation_async(
                            admin_id=admin_id,
                            conversation_id=conversation_id,
                            message=admin_reply_message,
                        )
                        return

                    elif message.language == "bn" or message.language == "ben":
                        admin_reply_message: str = (
                            await self.openai_service.translate_message_from_english_to_bengali_async(
                                message=clean_message
                            )
                        )
                        await self.intercom_service.add_admin_message_to_conversation_async(
                            admin_id=admin_id,
                            conversation_id=conversation_id,
                            message=admin_reply_message,
                        )
                        return
                    else:
                        return
        else:
            return

    async def handle_conversation_admin_assigned(self, data: Dict):
        print("conversation.admin.assigned")
