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


class ConversationStatus(Enum):
    STARTED = "started"
    STOPPED = "stoped"


class Language(Enum):
    ENGLISH = "English"
    HINDI = "Hindi"
    HINGLISH = "Hinglish"
    BENGALI = "Bengali"


class MessageStatus(Enum):
    NO_ERROR = "no_error"
    ERROR_FIXED = "error_fixed"
    UNCERTAIN = "uncertain"


class PayloadData(BaseModel):
    conversation_id: str
    clean_message: str


class UserRepliedHandler:
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

    async def user_replied_handler(self, payload: Dict):
        try:
            payload_params: PayloadData = self._get_payload_params(payload=payload)
            conversation_state: ConversationState = (
                await self.messages_cache_service.get_conversation_state(
                    conversation_id=payload_params.conversation_id
                )
            )
            if (
                conversation_state.conversation_status
                == ConversationStatus.STOPPED.value
            ):
                conversation_state.conversation_last_message = (
                    payload_params.clean_message
                )
                await self._update_conversation_status(
                    conversation_state=conversation_state
                )
                return

            if (
                conversation_state.conversation_status
                == ConversationStatus.STARTED.value
            ):

                user_replied_message_language: str = (
                    await self.translations_service.detect_language_async_v2(
                        message=payload_params.clean_message
                    )
                )

                conversation_state.conversation_language = user_replied_message_language
                if user_replied_message_language == Language.ENGLISH.value:
                    conversation_state.conversation_last_message = (
                        payload_params.clean_message
                    )
                    await self._update_conversation_status(
                        conversation_state=conversation_state
                    )
                    return
                if user_replied_message_language in [
                    Language.HINDI.value,
                    Language.HINGLISH.value,
                    Language.BENGALI.value,
                ]:
                    note_for_admin, context_analys = await self._get_note_for_admin(
                        user_replied_message=payload_params.clean_message,
                        current_context_analys=conversation_state.conversation_context_analys,
                    )
                    conversation_state.conversation_context_analys = context_analys
                    conversation_state.conversation_last_message = (
                        payload_params.clean_message
                    )
                    conversation_state.conversation_language = (
                        user_replied_message_language
                    )
                    await self._update_conversation_status(
                        conversation_state=conversation_state
                    )
                    await self.intercom_api_service.add_admin_note_to_conversation_async(
                        conversation_id=payload_params.conversation_id,
                        admin_id="8459322",
                        note=note_for_admin,
                    )
                    return
        except (ClientResponseError, RedisError, OpenAIError) as e:
            full_exception_name = f"{type(e).__module__}.{type(e).__name__}"
            exception_message: str = str(e)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.replied",
                params={"conversation_id": payload_params.conversation_id},
            )
            raise app_exception
        except Exception as ex:
            raise ex

    async def _update_conversation_status(self, conversation_state: ConversationState):
        await self.messages_cache_service.set_conversation_state(
            conversation_id=conversation_state.conversation_id,
            conversation_state=conversation_state,
        )

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

    def _get_payload_params(self, payload: Dict) -> PayloadData:
        user_reply: Dict = payload["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = user_reply.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        conversation_id: str = payload["data"]["item"]["id"]
        return PayloadData(conversation_id=conversation_id, clean_message=clean_message)
