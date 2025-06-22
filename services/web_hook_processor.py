from typing import Dict
from services.mongodb_service import MongodbService
from services.openai_api_service import OpenAIService
from bs4 import BeautifulSoup
from services.claude_ai import ClaudeService
from services.intercom_api_service import IntercomAPIService
from models.models import (
    User,
    UserMessage,
    MessageTranslated,
    ConversationMessage,
    ConversationMessages,
    RequestInfo,
    ConversationContext,
)
from models.custom_exceptions import APPException
from tasks import mongodb_task_async, translate_message_for_admin_bengali
import datetime
from services.conversation_parts_service import ConversationPartsService
from services.redis_cache_service import MessagesCache
from services.openai_translator_service import OpenAITranslatorService
from typing import List
from aiohttp.client_exceptions import ClientResponseError
from openai._exceptions import OpenAIError
from redis.exceptions import RedisError
from services.es_service import ESService
import time
import os
from prometheus_metricks.metricks import (
    USER_REPLIED_DURATION,
    ADMIN_NOTED_DURATION,
    USER_CREATED_DURATION,
    START_TRANSLATION_SERVICE_DURATION
)


class WebHookProcessor:

    def __init__(
            self,
            mongo_db_service: MongodbService,
            openai_service: OpenAIService,
            intercom_service: IntercomAPIService,
            conversation_parts_service: ConversationPartsService,
            messages_cache_service: MessagesCache,
            translations_service: OpenAITranslatorService,
            es_service: ESService,
            claude_ai_service: ClaudeService,
    ):
        self.mongo_db_service = mongo_db_service
        self.openai_service = openai_service
        self.intercom_service = intercom_service
        self.conversation_parts_service = conversation_parts_service
        self.messages_cache_service = messages_cache_service
        self.translations_service = translations_service
        self.es_service = es_service
        self.claude_ai_service = claude_ai_service

    async def process_message(self, topic: str, message: Dict):
        conversation_id: str = message.get("data", {}).get("item", {}).get("id", "")
        conv_status: str | None = self.messages_cache_service.get_conversation_status(
            conversation_id=conversation_id
        )

        if topic == "conversation.user.created":
            start_time = time.time()
            start_time2 = time.perf_counter()
            user_data: Dict = message.get("data", {}).get("item", {}).get("source", {})
            user_message: str = user_data.get("body", "")
            clean_message: str = BeautifulSoup(user_message, "html.parser").getText()

            # await self.handle_conversation_user_created_v2(data=message)

            await self.set_conversation_status(
                conversation_id=conversation_id, status="stoped"
            )
            # conv_context: ConversationContext = ConversationContext(last_user_message='', current_context_analys='')
            # self.messages_cache_service.set_conversation_context(conversation_id=conversation_id,
            #                                                      conversation_context=conv_context)
            self.messages_cache_service.set_conversation_analis(
                "conv_analys:" + conversation_id, analys=""
            )
            self.messages_cache_service.set_conversation_last_message(
                conversation_id=conversation_id, message=clean_message
            )

            USER_CREATED_DURATION.labels(
                pod_name=os.environ.get("HOSTNAME", "unknown")
            ).observe(time.time() - start_time)

            return

        elif topic == "conversation.user.replied":
            if conv_status == "stoped" or conv_status is None:
                user_reply: Dict = message["data"]["item"]["conversation_parts"][
                    "conversation_parts"
                ][0]
                user_message: str = user_reply.get("body", "")
                clean_message: str = BeautifulSoup(
                    user_message, "html.parser"
                ).getText()

                self.messages_cache_service.set_conversation_last_message(
                    conversation_id=conversation_id, message=clean_message
                )
                return
            start_time = time.time()
            await self.handle_conversation_user_replied_v3(data=message)
            USER_REPLIED_DURATION.labels(
                pod_name=os.environ.get("HOSTNAME", "unknown")
            ).observe(time.time() - start_time)
            return

        elif topic == "conversation.admin.replied":
            await self.handle_conversation_admin_replied(data=message)
            return

        elif topic == "conversation.admin.noted":
            admin_note: Dict = message["data"]["item"]["conversation_parts"][
                "conversation_parts"
            ][0]
            admin_message: str = admin_note.get("body", "")
            clean_message: str = BeautifulSoup(admin_message, "html.parser").getText()
            if (clean_message.startswith("!") == False):
                return

            start_time = time.time()
            await self.handle_conversation_admin_noted_v3(data=message)
            ADMIN_NOTED_DURATION.labels(
                pod_name=os.environ.get("HOSTNAME", "unknown")
            ).observe(time.time() - start_time)
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
        self.messages_cache_service.delete_conversation(
            conversation_id="conv:" + conversation_id
        )
        self.messages_cache_service.delete_conversation(
            "conv_status:" + conversation_id
        )
        self.messages_cache_service.delete_conversation(conversation_id='conv_analys:' + conversation_id)
        self.messages_cache_service.delete_conversation(conversation_id='conv_last_message:' + conversation_id)

    async def handle_conversation_user_created_v3(self, data: Dict):
        try:
            start_time = time.perf_counter()
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
            conv_message: ConversationMessage = ConversationMessage(
                conversation_id=conversation_id,
                time=datetime.datetime.now(),
                message=clean_message,
                user=user,
                language=message_language,
                message_type="conversation.user.created",
            )
            # await self.save_first_message_to_cache(
            #     conversation_id=conversation_id, message=message
            # )
            if message_language == "English":
                self.messages_cache_service.set_conversation_language(
                    conversation_id=conversation_id, language=message_language
                )
                conv_message.translated_en = clean_message
                await self.save_first_message_to_cache(
                    conversation_id=conversation_id, message=conv_message
                )
                await self.save_request_info(
                    status="ok",
                    execution_time=time.perf_counter() - start_time,
                    event_type="conversation.user.created(english)",
                )

            if message_language in ["Hindi", "Hinglish", "Bengali"]:
                self.messages_cache_service.set_conversation_language(
                    conversation_id=conversation_id, language=message_language
                )
                analyzed_user_message: UserMessage = (
                    await self.openai_service.analyze_message_with_correction_v3(
                        message=clean_message, conversation_id="conv:" + conversation_id
                    )
                )
                original_message = analyzed_user_message.original_text
                corrected_message = analyzed_user_message.corrected_text
                translated_text = analyzed_user_message.translated_text
                context_analysis = analyzed_user_message.context_analysis
                conv_message.translated_en = translated_text
                await self.save_first_message_to_cache(
                    conversation_id=conversation_id, message=conv_message
                )

                if analyzed_user_message.status == "no_error":
                    if message_language == "Hindi":
                        await self.send_admin_note_async(
                            conversation_id=conversation_id,
                            message=clean_message,
                            message_language=message_language,
                        )
                        await self.save_request_info(
                            status="ok",
                            execution_time=time.perf_counter() - start_time,
                            event_type="conversation.user.created",
                        )

                    elif message_language == "Hinglish":
                        await self.send_admin_note_async(
                            conversation_id=conversation_id,
                            message=clean_message,
                            message_language=message_language,
                        )
                        await self.save_request_info(
                            status="ok",
                            execution_time=time.perf_counter() - start_time,
                            event_type="conversation.user.created",
                        )

                    elif message_language == "Bengali":
                        await self.send_admin_note_async(
                            conversation_id=conversation_id,
                            message=clean_message,
                            message_language=message_language,
                        )
                        await self.save_request_info(
                            status="ok",
                            execution_time=time.perf_counter() - start_time,
                            event_type="conversation.user.created",
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
                        await self.save_request_info(
                            status="ok",
                            execution_time=time.perf_counter() - start_time,
                            event_type="conversation.user.created",
                        )
                    if message_language == "Hinglish":
                        await self.send_admin_note_async(
                            conversation_id=conversation_id,
                            message=corrected_message,
                            message_language=message_language,
                        )
                        await self.save_request_info(
                            status="ok",
                            execution_time=time.perf_counter() - start_time,
                            event_type="conversation.user.created",
                        )
                    if message_language == "Bengali":
                        await self.send_admin_note_async(
                            conversation_id=conversation_id,
                            message=corrected_message,
                            message_language=message_language,
                        )
                        await self.save_request_info(
                            status="ok",
                            execution_time=time.perf_counter() - start_time,
                            event_type="conversation.user.created",
                        )
                elif analyzed_user_message.status == "uncertain":
                    note: str = await self.create_admin_note(analyzed_user_message)

                    await self.send_admin_note_async(
                        conversation_id=conversation_id,
                        message=note,
                        message_language="English",
                    )
                    await self.save_request_info(
                        status="ok",
                        execution_time=time.perf_counter() - start_time,
                        event_type="conversation.user.created",
                    )
        except ClientResponseError as client_response_error:
            full_exception_name = f"{type(client_response_error).__module__}.{type(client_response_error).__name__}"
            exception_message: str = str(client_response_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.created",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
        except OpenAIError as open_ai_error:
            full_exception_name = (
                f"{type(open_ai_error).__module__}.{type(open_ai_error).__name__}"
            )
            exception_message: str = str(open_ai_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.created",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
        except RedisError as redis_error:
            full_exception_name = (
                f"{type(redis_error).__module__}.{type(redis_error).__name__}"
            )
            exception_message: str = str(redis_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.created",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
        except Exception as e:
            raise e

    async def send_admin_note_async(
            self, conversation_id: str, message: str, message_language, original: str
    ):
        admin_id: str = "8024055"
        # admin_id: str = "4687718"
        if message_language == "Hindi":
            note_for_admin: str = (
                await self.translations_service.translate_message_from_hindi_to_english_async(
                    message=message
                )
            )
            note_for_admin = "original:" + original + "\n" + "\n" + note_for_admin
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
            note_for_admin = "original:" + original + "\n" + "\n" + note_for_admin
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
            note_for_admin = "original:" + original + "\n" + "\n" + note_for_admin
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                note=note_for_admin,
            )
            return
        elif message_language == "English":
            note_for_admin = "original:" + original + "\n" + "\n" + message
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id, admin_id=admin_id, note=note_for_admin
            )
            return
        else:
            return

    async def create_admin_note(self, message: UserMessage):
        possible_interpritations = message.possible_interpretations
        one: str = possible_interpritations[0]
        two: str = possible_interpritations[1]
        note: str = (
                "translated: "
                + message.translated_text
                + "\n"
                + message.context_analysis
                + "\n"
                + one
                + "\n"
                + two
        )
        return note

    async def create_admin_note_v2(self, message: UserMessage):
        possible_interpritations = message.possible_interpretations
        interpretations: str = ""
        for interpretation in possible_interpritations:
            interpretations = interpretations + interpretation + "\n"

        note: str = (
                "translated: "
                + message.translated_text
                + "\n"
                + message.context_analysis
                + "\n"
                + "interpretations:"
                + "\n"
                + interpretations
        )
        return note

    async def create_admin_note_v2(self, message: UserMessage):
        possible_interpritations = message.possible_interpretations
        one: str = possible_interpritations[0]
        two: str = possible_interpritations[1]
        note: str = (
                "translated: "
                + message.translated_text
                + "\n"
                + message.note
                + "\n"
                + one
                + "\n"
                + two
        )
        return note

    async def save_request_info(
            self, status: str, execution_time: float, event_type: str
    ):
        request_info: RequestInfo = RequestInfo(
            status=status,
            execution_time=execution_time,
            event_type=event_type,
            exception=None,
        )

        self.es_service.add_document(
            index_name="requests", document=request_info.dict()
        )

        # es_client: ESService = ESService()
        # es_client.add_document(index_name="requests", document=request_info.dict())

    async def save_first_message_to_cache(
            self, conversation_id: str, message: ConversationMessage
    ):
        messages: ConversationMessages = ConversationMessages(messages=[message])
        self.messages_cache_service.set_conversation_messages(
            conversation_id="conv:" + conversation_id, messages=messages
        )

    async def save_first_message_to_cache_2(
            self,
            conversation_id: str,
            message: ConversationMessage,
            analyzed_message: UserMessage,
    ):
        translated_message: str = analyzed_message.translated_text
        if analyzed_message.status == "no_error":
            message.translated_en = translated_message
            messages: ConversationMessages = ConversationMessages(messages=[message])
            self.messages_cache_service.set_conversation_messages(
                conversation_id="conv:" + conversation_id, messages=messages
            )

    async def save_message_to_cache(
            self, conversation_id: str, message: ConversationMessage
    ):
        all_conversation_messages = (
            self.messages_cache_service.get_conversation_messages(
                conversation_id="conv:" + conversation_id
            )
        )
        if all_conversation_messages == None:
            await self.save_first_message_to_cache(
                conversation_id=conversation_id, message=message
            )
            return

        all_conversation_messages.messages.append(message)
        self.messages_cache_service.set_conversation_messages(
            conversation_id="conv:" + conversation_id,
            messages=all_conversation_messages,
        )

    async def set_conversation_status(self, conversation_id: str, status: str):
        self.messages_cache_service.set_conversation_status(
            conversation_d=conversation_id, status=status
        )

    async def handle_conversation_user_created_v2(self, data: Dict):
        conversation_id: str = data.get("data", {}).get("item", {}).get("id", "")
        # self.intercom_service.attach_admin_to_conversation(
        #     conversation_id=conversation_id, admin_id=8028082
        # )
        user_data: Dict = data.get("data", {}).get("item", {}).get("source", {})
        message: str = user_data.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        user_id: str = data.get("author", {}).get("id", "")
        user_email: str = data.get("author", {}).get("email", "")

        user: User = User(id=user_id, email=user_email, type="user")

        analyzed_message: UserMessage = (
            await self.openai_service.analyze_message_with_correction(
                message=clean_message
            )
        )
        message_language_code: str = analyzed_message.language
        self.messages_cache_service.set_conversation_language(
            conversation_id=conversation_id, language=message_language_code
        )

        # message_language_code: str = (
        #     await self.translations_service.detect_language_async_v2(
        #         message=clean_message
        #     )
        # )

        # message: ConversationMessage = ConversationMessage(
        #     conversation_id=conversation_id,
        #     time=datetime.datetime.now(),
        #     message=clean_message,
        #     user=user,
        #     language=message_language_code,
        #     message_type="conversation.user.created",
        # )
        # messages: ConversationMessages = ConversationMessages(messages=[message])
        # self.messages_cache_service.set_conversation_messages(
        #     conversation_id=conversation_id, messages=messages
        # )

        if message_language_code == "English":
            return
        if message_language_code in ["Hindi", "Hinglish", "Bengali"]:
            # analyzed_message: UserMessage = (
            #     await self.openai_service.analyze_message_with_correction(
            #         message=clean_message
            #     )
            # )
            if analyzed_message.status == "no_error":
                note_for_admin: str = (
                        "original:"
                        + analyzed_message.original_text
                        + "\n"
                        + "\n"
                        + analyzed_message.translated_text
                )
                await self.intercom_service.add_admin_note_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id="8024055",
                    note=note_for_admin,
                )
            elif analyzed_message.status == "error_fixed":
                note_for_admin: str = (
                        "original:"
                        + analyzed_message.original_text
                        + "\n"
                        + "\n"
                        + analyzed_message.corrected_text
                )
                await self.intercom_service.add_admin_note_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id="8024055",
                    note=note_for_admin,
                )
            elif analyzed_message.status == "uncertain":
                note_for_admin: str = await self.create_admin_note_v2(
                    message=analyzed_message
                )
                note_for_admin = (
                        "original:"
                        + analyzed_message.original_text
                        + "\n"
                        + "\n"
                        + note_for_admin
                )
                await self.intercom_service.add_admin_note_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id="8024055",
                    note=note_for_admin,
                )
            else:

                return

    async def handle_conversation_user_replied_v3(self, data: Dict):
        try:

            start_time = time.perf_counter()

            user_reply: Dict = data["data"]["item"]["conversation_parts"][
                "conversation_parts"
            ][0]
            message: str = user_reply.get("body", "")
            clean_message: str = BeautifulSoup(message, "html.parser").getText()
            user_email: str = user_reply.get("author", {}).get("email", "")
            user_id: str = user_reply.get("author", {}).get("id", "")
            admin_id: str = "4687718"
            conversation_id: str = data["data"]["item"]["id"]
            start_detect = time.perf_counter()
            message_language: str = (
                await self.translations_service.detect_language_async_v2(
                    message=clean_message
                )
            )
            print(time.perf_counter() - start_detect)
            # user: User = User(id=user_id, email=user_email, type="user")
            # conv_message: ConversationMessage = ConversationMessage(
            #     conversation_id=conversation_id,
            #     time=datetime.datetime.now(),
            #     message=clean_message,
            #     user=user,
            #     language=message_language,
            #     message_type="conversation.user.replied",
            # )
            # await self.save_message_to_cache(
            #     conversation_id=conversation_id, message=message
            # )
            if message_language == "English":
                self.messages_cache_service.set_conversation_language(
                    conversation_id=conversation_id, language=message_language
                )
                # conv_message.translated_en = clean_message
                # await self.save_message_to_cache(
                #     conversation_id=conversation_id, message=conv_message
                # )

                await self.save_request_info(
                    status="ok",
                    execution_time=time.perf_counter() - start_time,
                    event_type="conversation.user.replied(english)",
                )

            if message_language in ["Hindi", "Hinglish", "Bengali"]:
                self.messages_cache_service.set_conversation_language(
                    conversation_id=conversation_id, language=message_language
                )

                current_analys: str = (
                    self.messages_cache_service.get_conversation_analis(
                        "conv_analys:" + conversation_id
                    )
                )
                # conv_context: ConversationContext = self.messages_cache_service.get_conversation_context(
                #     conversation_id=conversation_id)
                analyzed_message: UserMessage = (
                    await self.openai_service.analyze_message_with_correction_v4(
                        message=clean_message, analys=current_analys
                    )
                )

                # self.messages_cache_service.set_conversation_context(conversation_id=conversation_id,
                #                                                      conversation_context=conv_context)
                self.messages_cache_service.set_conversation_analis(
                    conversation_id="conv_analys:" + conversation_id,
                    analys=analyzed_message.context_analysis,
                )

                # conv_message.translated_en = analyzed_message.translated_text
                # await self.save_message_to_cache(
                #     conversation_id=conversation_id, message=conv_message
                # )
                if analyzed_message.status == "no_error":
                    if message_language != "English":
                        note_for_admin: str = (
                                "original:"
                                + clean_message
                                + "\n\n"
                                + analyzed_message.translated_text
                        )
                        await self.intercom_service.add_admin_note_to_conversation_async(
                            conversation_id=conversation_id,
                            admin_id=admin_id,
                            note=note_for_admin,
                        )
                        print(f"user.replied:{time.perf_counter() - start_time}")

                        # await self.send_admin_note_async(
                        #     conversation_id=conversation_id,
                        #     message=clean_message,
                        #     message_language=message_language,
                        #     original=clean_message,
                        # )
                        # await self.save_request_info(
                        #     status="ok",
                        #     execution_time=time.perf_counter() - start_time,
                        #     event_type="conversation.user.replied",
                        # )
                if analyzed_message.status == "error_fixed":
                    corrected_message: str = analyzed_message.corrected_text
                    note_for_admin: str = (
                            "original:"
                            + analyzed_message.original_text
                            + "\n\n"
                            + analyzed_message.translated_text
                    )
                    await self.intercom_service.add_admin_note_to_conversation_async(
                        conversation_id=conversation_id,
                        admin_id=admin_id,
                        note=note_for_admin,
                    )
                    print(f"user.replied:{time.perf_counter() - start_time}")

                    # await self.send_admin_note_async(
                    #     conversation_id=conversation_id,
                    #     message=corrected_message,
                    #     message_language=message_language,
                    #     original=clean_message,
                    # )
                    # await self.save_request_info(
                    #     status="ok",
                    #     execution_time=time.perf_counter() - start_time,
                    #     event_type="conversation.user.replied",
                    # )

                if analyzed_message.status == "uncertain":
                    note: str = await self.create_admin_note(analyzed_message)
                    note_for_admin: str = (
                            "original:" + analyzed_message.original_text + "\n\n" + note
                    )
                    note_time = time.perf_counter()
                    await self.intercom_service.add_admin_note_to_conversation_async(
                        conversation_id=conversation_id,
                        admin_id=admin_id,
                        note=note_for_admin,
                    )
                    print(time.perf_counter() - note_time)
                    print(f"user.replied:{time.perf_counter() - start_time}")

                    # await self.send_admin_note_async(
                    #     conversation_id=conversation_id,
                    #     message=note,
                    #     message_language="English",
                    #     original=clean_message,
                    # )
                    # await self.save_request_info(
                    #     status="ok",
                    #     execution_time=time.perf_counter() - start_time,
                    #     event_type="conversation.user.replied",
                    # )
            return
        except ClientResponseError as client_response_error:
            full_exception_name = f"{type(client_response_error).__module__}.{type(client_response_error).__name__}"
            exception_message: str = str(client_response_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.replied",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
        except OpenAIError as open_ai_error:
            full_exception_name = (
                f"{type(open_ai_error).__module__}.{type(open_ai_error).__name__}"
            )
            exception_message: str = str(open_ai_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.replied",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
        except RedisError as redis_error:
            full_exception_name = (
                f"{type(redis_error).__module__}.{type(redis_error).__name__}"
            )
            exception_message: str = str(redis_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.replied",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
        except Exception as e:
            raise e

    async def handle_conversation_user_replied_v2(self, data: Dict):
        user_reply: Dict = data["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = user_reply.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        user_email: str = user_reply.get("author", {}).get("email", "")
        user_id: str = user_reply.get("author", {}).get("id", "")
        conversation_id: str = data["data"]["item"]["id"]
        # message_language_code: str = await self.openai_service.detect_language_async(
        #     clean_message
        # )

        user: User = User(id=user_id, email=user_email, type="user")
        analyzed_message: UserMessage = (
            await self.openai_service.analyze_message_with_correction(
                message=clean_message
            )
        )
        message_language_code: str = analyzed_message.language
        self.messages_cache_service.set_conversation_language(
            conversation_id=conversation_id, language=message_language_code
        )
        # message: ConversationMessage = ConversationMessage(
        #     conversation_id=conversation_id,
        #     time=datetime.datetime.now(),
        #     message=clean_message,
        #     user=user,
        #     language=message_language_code,
        #     message_type="conversation.user.replied",
        # )
        # all_messages: ConversationMessages = (
        #     self.messages_cache_service.get_conversation_messages(
        #         conversation_id=conversation_id
        #     )
        # )
        # all_messages.messages.append(message)
        # self.messages_cache_service.set_conversation_messages(
        #     conversation_id=conversation_id, messages=all_messages
        # )
        if message_language_code == "English":
            return
        if message_language_code in ["Hindi", "Hinglish", "Bengali"]:
            # analyzed_message: UserMessage = (
            #     await self.openai_service.analyze_message_with_correction(
            #         message=clean_message
            #     )
            # )
            if analyzed_message.status == "no_error":
                note_for_admin: str = (
                        "original:"
                        + analyzed_message.original_text
                        + "\n"
                        + "\n"
                        + analyzed_message.translated_text
                )
                await self.intercom_service.add_admin_note_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id="8024055",
                    note=note_for_admin,
                )
            elif analyzed_message.status == "error_fixed":
                note_for_admin: str = (
                        "original:"
                        + analyzed_message.original_text
                        + "\n"
                        + "\n"
                        + analyzed_message.corrected_text
                )
                await self.intercom_service.add_admin_note_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id="8024055",
                    note=note_for_admin,
                )
            elif analyzed_message.status == "uncertain":
                note_for_admin: str = await self.create_admin_note_v2(
                    message=analyzed_message
                )
                note_for_admin = (
                        "original:"
                        + analyzed_message.original_text
                        + "\n"
                        + "\n"
                        + note_for_admin
                )
                await self.intercom_service.add_admin_note_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id="8024055",
                    note=note_for_admin,
                )
            else:

                return

    async def handle_conversation_admin_replied(self, data: Dict):

        print("conversation.admin.replied")

    async def handle_conversation_admin_noted_v3(self, data: Dict):
        try:

            start_time = time.perf_counter()
            print("conversation.admin.noted")

            admin_note: Dict = data["data"]["item"]["conversation_parts"][
                "conversation_parts"
            ][0]
            message: str = admin_note.get("body", "")
            clean_message: str = BeautifulSoup(message, "html.parser").getText()
            admin_id: str = admin_note.get("author", {}).get("id", "")
            conversation_id: str = data["data"]["item"]["id"]
            conv_status: str | None = (
                self.messages_cache_service.get_conversation_status(
                    conversation_id=conversation_id
                )
            )
            is_note_for_reply: bool = clean_message.startswith("!")
            conversation_language: str | None = (
                self.messages_cache_service.get_conversation_language(
                    conversation_id=conversation_id
                )
            )
            if clean_message.startswith("!force") == True:
                conv_lang: str = clean_message.split("!force", 1)[1].strip()

                conv_language: str = ""
                if conv_lang == "hi":
                    conv_language = "Hinglish"
                elif conv_lang == "bn":
                    conv_language = "Bengali"
                elif conv_lang == "hindi":
                    conv_language = "Hindi"
                else:
                    return

                self.messages_cache_service.set_conversation_language(
                    conversation_id=conversation_id, language=conv_language
                )
                await self.set_conversation_status(
                    conversation_id=conversation_id, status="started"
                )
                last_message: str | None = (
                    self.messages_cache_service.get_conversation_last_message(
                        conversation_id=conversation_id
                    )
                )
                if last_message is None:
                    return
                else:
                    await self.start_translation_service(
                        conversation_id=conversation_id, message=last_message
                    )
                    return
            if clean_message in ["!detect lang", "!start", "!stop", "!detect start"]:
                if clean_message == "!stop":
                    await self.set_conversation_status(
                        conversation_id=conversation_id, status="stoped"
                    )
                    return
                if (clean_message == "!detect start"):
                    await self.set_conversation_status(conversation_id=conversation_id, status="started")
                    last_chat_message: str | None = (
                        self.messages_cache_service.get_conversation_last_message(
                            conversation_id=conversation_id
                        )
                    )
                    if last_chat_message is not None:
                        chat_lang: str = (
                            await self.translations_service.detect_language_async_v2(
                                message=last_chat_message
                            )
                        )
                        self.messages_cache_service.set_conversation_language(
                            conversation_id=conversation_id, language=chat_lang
                        )
                        return
                    else:
                        self.messages_cache_service.set_conversation_language(conversation_id=conversation_id,
                                                                              language="Hinglish")
                        return

                if clean_message == "!start":
                    await self.set_conversation_status(
                        conversation_id=conversation_id, status="started"
                    )
                    current_conv_language: str = (
                        self.messages_cache_service.get_conversation_language(
                            conversation_id=conversation_id
                        )
                    )
                    if current_conv_language is None:
                        self.messages_cache_service.set_conversation_language(
                            conversation_id=conversation_id, language="Hinglish"
                        )

                    return
                if clean_message == "!detect lang":
                    last_chat_message: str | None = (
                        self.messages_cache_service.get_conversation_last_message(
                            conversation_id=conversation_id
                        )
                    )
                    if last_chat_message is not None:
                        chat_lang: str = (
                            await self.translations_service.detect_language_async_v2(
                                message=last_chat_message
                            )
                        )
                        self.messages_cache_service.set_conversation_language(
                            conversation_id=conversation_id, language=chat_lang
                        )
                        return

            if is_note_for_reply == True and conv_status != "stoped":
                clean_message = clean_message.lstrip("!")
                user: User = User(id=admin_id, email="em@gmail.com", type="admin")

                # conv_message: ConversationMessage = ConversationMessage(
                #     conversation_id=conversation_id,
                #     time=datetime.datetime.now(),
                #     message=clean_message,
                #     user=user,
                #     language="English",
                #     message_type="conversation.admin.noted",
                # )
                # await self.save_message_to_cache(
                #     conversation_id=conversation_id, message=conv_message
                # )

                await self.send_admin_reply_message(
                    conversation_id=conversation_id,
                    admin_id=admin_id,
                    target_language=conversation_language,
                    message=clean_message,
                    user=user,
                )
                await self.save_request_info(
                    status="ok",
                    execution_time=time.perf_counter() - start_time,
                    event_type="conversation.admin.noted",
                )
            else:
                return
        except ClientResponseError as client_response_error:
            full_exception_name = f"{type(client_response_error).__module__}.{type(client_response_error).__name__}"
            exception_message: str = str(client_response_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.admin.noted",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
        except OpenAIError as open_ai_error:
            full_exception_name = (
                f"{type(open_ai_error).__module__}.{type(open_ai_error).__name__}"
            )
            exception_message: str = str(open_ai_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.admin.noted",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
        except RedisError as redis_error:
            full_exception_name = (
                f"{type(redis_error).__module__}.{type(redis_error).__name__}"
            )
            exception_message: str = str(redis_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.admin.noted",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
        except Exception as e:
            raise e

    async def start_translation_service(self, conversation_id: str, message: str):
        start_time = time.time()
        admin_id: str = "4687718"
        current_analys: str = self.messages_cache_service.get_conversation_analis(
            "conv_analys:" + conversation_id
        )
        analyzed_message: UserMessage = (
            await self.openai_service.analyze_message_with_correction_v4(
                message=message, analys=current_analys
            )
        )
        self.messages_cache_service.set_conversation_analis(
            "conv_analys:" + conversation_id, analys=analyzed_message.context_analysis
        )
        if analyzed_message.status == "no_error":
            note_for_admin: str = (
                    "original:" + message + "\n\n" + analyzed_message.translated_text
            )
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                note=note_for_admin,
            )

        elif analyzed_message.status == "error_fixed":

            note_for_admin: str = (
                    "original:"
                    + analyzed_message.original_text
                    + "\n\n"
                    + analyzed_message.translated_text
            )
            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                note=note_for_admin,
            )
        elif analyzed_message.status == "uncertain":
            note: str = await self.create_admin_note(analyzed_message)
            note_for_admin: str = (
                    "original:" + analyzed_message.original_text + "\n\n" + note
            )

            await self.intercom_service.add_admin_note_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                note=note_for_admin,
            )
        else:
            return
        START_TRANSLATION_SERVICE_DURATION.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).observe(
            time.time() - start_time)
        return

    async def send_admin_reply_message(
            self,
            user: User,
            conversation_id: str,
            admin_id: str,
            message: str,
            target_language: str,
    ):
        if target_language == None:
            return
        # conv_message: ConversationMessage = ConversationMessage(
        #     conversation_id=conversation_id,
        #     time=datetime.datetime.now(),
        #     message=message,
        #     user=user,
        #     language="English",
        #     message_type="conversation.admin.noted",
        # )
        current_analys: str = self.messages_cache_service.get_conversation_analis(
            conversation_id="conv_analys:" + conversation_id
        )

        new_context_analys: str = await self.openai_service.analyze_agent_message(
            agent_message=message,
            context_analys=current_analys,
        )
        self.messages_cache_service.set_conversation_analis(
            conversation_id="conv_analys:" + conversation_id, analys=new_context_analys
        )

        if target_language == "Hinglish":
            admin_reply_message: str = (
                await self.translations_service.translate_message_from_english_to_hinglish_async_v2(
                    message=message
                )
            )
            # conv_message.translated_en = admin_reply_message
            await self.intercom_service.add_admin_message_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                message=admin_reply_message,
            )
            # await self.save_message_to_cache(
            #     conversation_id=conversation_id, message=conv_message
            # )
            return
        elif target_language == "Hindi":
            admin_reply_message: str = (
                await self.translations_service.translate_message_from_english_to_hindi_async(
                    message=message
                )
            )
            # conv_message.translated_en = admin_reply_message
            await self.intercom_service.add_admin_message_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                message=admin_reply_message,
            )
            # await self.save_message_to_cache(
            #     conversation_id=conversation_id, message=conv_message
            # )
            return
        elif target_language == "Bengali":
            admin_reply_message: str = (
                await self.translations_service.translate_message_from_english_to_bengali_async(
                    message=message
                )
            )
            # conv_message.translated_en = admin_reply_message
            await self.intercom_service.add_admin_message_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                message=admin_reply_message,
            )
            # await self.save_message_to_cache(
            #     conversation_id=conversation_id, message=conv_message
            # )
            return
        elif target_language == "English":
            await self.intercom_service.add_admin_message_to_conversation_async(
                conversation_id=conversation_id,
                admin_id=admin_id,
                message=message,
            )
            # conv_message.translated_en = message
            # await self.save_message_to_cache(
            #     conversation_id=conversation_id, message=conv_message
            # )
            return
        else:
            return

    async def handle_conversation_admin_noted_v2(self, data: Dict):
        admin_translator_id: str = "8024055"
        admin_note: Dict = data["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = admin_note.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        admin_id: str = admin_note.get("author", {}).get("id", "")
        conversation_id: str = data["data"]["item"]["id"]
        conversation_language: str | None = (
            self.messages_cache_service.get_conversation_language(
                conversation_id=conversation_id
            )
        )
        is_note_for_reply: bool = clean_message.startswith("!")
        if is_note_for_reply == True:
            if conversation_language == "Hinglish":
                admin_reply_message: str = (
                    await self.translations_service.translate_message_from_english_to_hinglish_async_v2(
                        message=message
                    )
                )

                await self.intercom_service.add_admin_message_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id=admin_id,
                    message=admin_reply_message,
                )

                return
            elif conversation_language == "Hindi":
                admin_reply_message: str = (
                    await self.translations_service.translate_message_from_english_to_hindi_async(
                        message=message
                    )
                )

                await self.intercom_service.add_admin_message_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id=admin_id,
                    message=admin_reply_message,
                )

                return
            elif conversation_language == "Bengali":
                admin_reply_message: str = (
                    await self.translations_service.translate_message_from_english_to_bengali_async(
                        message=message
                    )
                )

                await self.intercom_service.add_admin_message_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id=admin_id,
                    message=admin_reply_message,
                )

                return
            elif conversation_language == "English":
                await self.intercom_service.add_admin_message_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id=admin_id,
                    message=message,
                )

                return
            else:
                return

    async def handle_conversation_admin_assigned(self, data: Dict):
        print("conversation.admin.assigned")
