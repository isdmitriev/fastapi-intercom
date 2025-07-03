from services.intercom_api_service import IntercomAPIService
from services.openai_api_service import OpenAIService
from services.openai_translator_service import OpenAITranslatorService
from services.redis_cache_service import MessagesCache
from services.handlers.common import MessageHandler
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
from services.handlers.models import MessageAnalysConfig, MessageAnalysResponse
import traceback


class ConversationStatus(Enum):
    STARTED = "started"
    STOPPED = "stoped"


class Language(Enum):
    ENGLISH = "English"
    HINDI = "Hindi"
    HINGLISH = "Hinglish"
    BENGALI = "Bengali"


class PayloadData(BaseModel):
    conversation_id: str
    clean_message: str


class UserRepliedHandler(MessageHandler):

    async def execute(self, payload: Dict):
        await self.user_replied_handler(payload=payload)

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
                await self.update_conversation_status(
                    conversation_state=conversation_state,
                    conversation_id=payload_params.conversation_id,
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
                    await self.update_conversation_status(
                        conversation_state=conversation_state,
                        conversation_id=payload_params.conversation_id,
                    )
                    return
                if user_replied_message_language in [
                    Language.HINDI.value,
                    Language.HINGLISH.value,
                    Language.BENGALI.value,
                ]:
                    analys_config: MessageAnalysConfig = MessageAnalysConfig(
                        message=payload_params.clean_message,
                        type="fast",
                        model="gpt-3.5-turbo-0125",
                        chat_context=conversation_state.conversation_context_analys,
                    )
                    analyze_result: MessageAnalysResponse = (
                        await self.message_analyze_service.analyze_message(
                            analys_config=analys_config
                        )
                    )

                    conversation_state.conversation_context_analys = (
                        analyze_result.chat_context_analys
                    )
                    conversation_state.conversation_last_message = (
                        payload_params.clean_message
                    )
                    conversation_state.conversation_language = (
                        user_replied_message_language
                    )
                    await self.update_conversation_status(
                        conversation_state=conversation_state,
                        conversation_id=payload_params.conversation_id,
                    )
                    await self.intercom_api_service.add_admin_note_to_conversation_async(
                        conversation_id=payload_params.conversation_id,
                        admin_id="8459322",
                        note=analyze_result.note_for_admin,
                    )
                    return
        except (ClientResponseError, RedisError, OpenAIError) as e:
            stack = traceback.format_exc()
            full_exception_name = f"{type(e).__module__}.{type(e).__name__}"
            exception_message: str = str(e)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.replied",
                params={"conversation_id": payload_params.conversation_id},
                stack_trace=stack
            )
            raise app_exception
        except Exception as ex:
            raise ex

    def _get_payload_params(self, payload: Dict) -> PayloadData:
        user_reply: Dict = payload["data"]["item"]["conversation_parts"][
            "conversation_parts"
        ][0]
        message: str = user_reply.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        conversation_id: str = payload["data"]["item"]["id"]
        return PayloadData(conversation_id=conversation_id, clean_message=clean_message)
