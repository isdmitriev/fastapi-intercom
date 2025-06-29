from services.intercom_api_service import IntercomAPIService
from services.openai_api_service import OpenAIService
from services.openai_translator_service import OpenAITranslatorService
from services.redis_cache_service import MessagesCache
from dependency_injector.wiring import inject
from typing import Dict, Tuple
from bs4 import BeautifulSoup
from pydantic import BaseModel
from models.models import ConversationState
from enum import Enum
from models.models import UserMessage
from models.custom_exceptions import APPException
from aiohttp.client_exceptions import ClientResponseError
from openai._exceptions import OpenAIError
from redis.exceptions import RedisError


class MessageStatus(Enum):
    NO_ERROR = "no_error"
    ERROR_FIXED = "error_fixed"
    UNCERTAIN = "uncertain"


class ConversationStatus(Enum):
    STARTED = "started"
    STOPPED = "stoped"


class AdminCommand(Enum):
    FORCEHI = "!force hi"
    FORCEHINDI = "!force hindi"
    FORCEBN = "!force bn"
    START = "!start"
    STOP = "!stop"
    DETECTSTART = "!detect start"


class CommandLanguage(Enum):
    en = "English"
    hindi = "Hindi"
    hi = "Hinglish"
    bn = "Bengali"


class PayloadData(BaseModel):
    conversation_id: str
    clean_message: str
    admin_id: str


class AdminNotedHandler:
    @inject
    def __init__(
            self,
            intercom_api_service: IntercomAPIService,
            open_ai_service: OpenAIService,
            messages_cache_service: MessagesCache,
            translations_service: OpenAITranslatorService,
    ):
        self.intercom_api_service = intercom_api_service
        self.open_ai_service = open_ai_service
        self.messages_cache_service = messages_cache_service
        self.translations_service = translations_service

    async def admin_noted_handler(self, payload: Dict):
        try:
            payload_params: PayloadData = self._get_payload_params(payload=payload)
            conversation_state: ConversationState | None = (
                await self.messages_cache_service.get_conversation_state(
                    conversation_id=payload_params.conversation_id
                )
            )
            if payload_params.clean_message == AdminCommand.START.value:
                conversation_state.conversation_status = ConversationStatus.STARTED.value
                await self._update_conversation_status(
                    conversation_state=conversation_state
                )
                return
            if payload_params.clean_message == AdminCommand.STOP.value:
                conversation_state.conversation_status = ConversationStatus.STOPPED.value
                await self._update_conversation_status(
                    conversation_state=conversation_state
                )
                return
            if payload_params.clean_message == AdminCommand.DETECTSTART.value:
                await self.start_translation_service(
                    admin_id=payload_params.admin_id, conversation_state=conversation_state
                )
                return
            if payload_params.clean_message in [
                AdminCommand.FORCEHI.value,
                AdminCommand.FORCEHINDI.value,
                AdminCommand.FORCEBN.value,
            ]:
                conversation_state.conversation_status = ConversationStatus.STARTED.value
                command_language: str = payload_params.clean_message.split("!force", 1)[
                    1
                ].strip()
                target_language: str = self._get_target_language(
                    command_language=command_language
                )
                conversation_state.conversation_status = ConversationStatus.STARTED.value
                conversation_state.conversation_language = target_language
                await self._update_conversation_status(
                    conversation_state=conversation_state
                )
                await self._start_force_lang(
                    admin_id=payload_params.admin_id, conversation_state=conversation_state
                )
                return

            if (
                    payload_params.clean_message.startswith("!")
                    and conversation_state.conversation_status
                    == ConversationStatus.STARTED.value
            ):

                message_for_user: str = payload_params.clean_message.lstrip("!")
                target_lang: str | None = conversation_state.conversation_language
                if target_lang is not None:
                    await self.send_admin_reply_message(
                        message=message_for_user,
                        admin_id=payload_params.admin_id,
                        conversation_id=payload_params.conversation_id,
                        target_lang=target_lang,
                        conv_state=conversation_state
                    )
                    return
        except (ClientResponseError, RedisError, OpenAIError) as e:
            full_exception_name = f"{type(e).__module__}.{type(e).__name__}"
            exception_message: str = str(e)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.created",
                params={"conversation_id": payload_params.conversation_id},
            )
            raise app_exception
        except Exception as ex:
            raise ex

    async def _start_force_lang(
            self, admin_id: str, conversation_state: ConversationState
    ):
        last_message: str | None = conversation_state.conversation_last_message
        note_for_admin, context_analys = await self._get_note_for_admin(
            last_message, conversation_state.conversation_context_analys
        )
        await self.intercom_api_service.add_admin_note_to_conversation_async(
            admin_id=admin_id,
            note=note_for_admin,
            conversation_id=conversation_state.conversation_id,
        )

    async def start_translation_service(
            self, admin_id: str, conversation_state: ConversationState
    ):
        last_message: str = conversation_state.conversation_last_message
        last_message_lang: str = (
            await self.translations_service.detect_language_async_v2(
                message=last_message
            )
        )

        note_for_admin, context_analys = await self._get_note_for_admin(
            user_replied_message=last_message,
            current_context_analys=conversation_state.conversation_context_analys,
        )
        conversation_state.conversation_context_analys = context_analys
        conversation_state.conversation_language = last_message_lang
        conversation_state.conversation_status = ConversationStatus.STARTED.value

        await self.intercom_api_service.add_admin_note_to_conversation_async(
            conversation_id=conversation_state.conversation_id,
            admin_id=admin_id,
            note=note_for_admin,
        )
        await self._update_conversation_status(conversation_state=conversation_state)

    async def _get_note_for_admin(
            self, user_replied_message: str, current_context_analys: str
    ) -> Tuple[str, str]:

        analyzed_user_message: UserMessage = (
            await self.open_ai_service.analyze_message_with_correction_v4(
                message=user_replied_message, analys=current_context_analys
            )
        )
        if analyzed_user_message.status == MessageStatus.NO_ERROR.value:
            note_for_admin: str = (
                    "original:"
                    + user_replied_message
                    + "\n\n"
                    + analyzed_user_message.translated_text
            )
            return (note_for_admin, analyzed_user_message.context_analysis)
        if analyzed_user_message.status == MessageStatus.ERROR_FIXED.value:
            note_for_admin: str = (
                    "original:"
                    + user_replied_message
                    + "\n\n"
                    + analyzed_user_message.corrected_text
            )
            return (note_for_admin, analyzed_user_message.context_analysis)
        if analyzed_user_message.status == MessageStatus.UNCERTAIN.value:
            note: str = self._create_admin_note_for_uncertain_status(
                analyzed_message=analyzed_user_message
            )
            note_for_admin: str = (
                    "original:" + analyzed_user_message.original_text + "\n\n" + note
            )
            return (note_for_admin, analyzed_user_message.context_analysis)

    def _create_admin_note_for_uncertain_status(
            self, analyzed_message: UserMessage
    ) -> str:
        possible_interpritations = analyzed_message.possible_interpretations
        one: str = possible_interpritations[0]
        two: str = possible_interpritations[1]
        note: str = (
                "translated: "
                + analyzed_message.translated_text
                + "\n"
                + analyzed_message.context_analysis
                + "\n"
                + one
                + "\n"
                + two
        )
        return note

    async def send_admin_reply_message(
            self,
            conv_state: ConversationState,
            message: str,
            admin_id: str,
            conversation_id: str,
            target_lang: str,
    ):
        if target_lang == None:
            return
        if target_lang == CommandLanguage.hi.value:
            admin_note: str = (
                await self.translations_service.translate_message_from_english_to_hinglish_async_v2(
                    message=message
                )
            )
        elif target_lang == CommandLanguage.hindi.value:
            admin_note: str = (
                await self.translations_service.translate_message_from_english_to_hindi_async(
                    message=message
                )
            )
        elif target_lang == CommandLanguage.bn.value:
            admin_note: str = (
                await self.translations_service.translate_message_from_english_to_bengali_async(
                    message=message
                )
            )
        else:
            return
        await self.intercom_api_service.add_admin_message_to_conversation_async(
            conversation_id=conversation_id, message=admin_note, admin_id=admin_id
        )
        new_context_analys: str = await self.open_ai_service.analyze_agent_message(
            agent_message=message, context_analys=conv_state.conversation_context_analys
        )
        conv_state.conversation_context_analys = new_context_analys
        await self._update_conversation_status(conversation_state=conv_state)

    def _get_target_language(self, command_language: str) -> str | None:
        if command_language == CommandLanguage.hi.name:
            return CommandLanguage.hi.value
        elif command_language == CommandLanguage.bn.name:
            return CommandLanguage.bn.value
        elif command_language == CommandLanguage.hindi.name:

            return CommandLanguage.hindi.value
        else:
            return None

    def _get_payload_params(self, payload: Dict) -> PayloadData:
        admin_note: Dict = payload["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = admin_note.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        admin_id: str = admin_note.get("author", {}).get("id", "")
        conversation_id: str = payload["data"]["item"]["id"]
        return PayloadData(
            conversation_id=conversation_id,
            admin_id=admin_id,
            clean_message=clean_message,
        )

    async def _update_conversation_status(self, conversation_state: ConversationState):
        await self.messages_cache_service.set_conversation_state(
            conversation_id=conversation_state.conversation_id,
            conversation_state=conversation_state,
        )
