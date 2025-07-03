from services.intercom_api_service import IntercomAPIService
from services.openai_api_service import OpenAIService
from services.openai_translator_service import OpenAITranslatorService
from services.redis_cache_service import MessagesCache
from dependency_injector.wiring import inject
from typing import Dict
from bs4 import BeautifulSoup
from pydantic import BaseModel
from models.models import ConversationState
from enum import Enum
from models.custom_exceptions import APPException
from aiohttp.client_exceptions import ClientResponseError
from openai._exceptions import OpenAIError
from redis.exceptions import RedisError
from services.handlers.common import MessageHandler
import traceback


class ConversationStatus(Enum):
    STARTED = "started"
    STOPPED = "stoped"


class PayloadData(BaseModel):
    conversation_id: str
    clean_message: str


class UserCreatedHandler(MessageHandler):

    async def execute(self, payload: Dict):
        await self.user_created_handler(payload=payload)

    async def user_created_handler(self, payload: Dict):
        try:
            payload_params: PayloadData = self._get_payload_params(payload=payload)
            conversation_state: ConversationState = ConversationState(
                conversation_id=payload_params.conversation_id,
                conversation_status=ConversationStatus.STOPPED.value,
                conversation_language=None,
                conversation_last_message=payload_params.clean_message,
                conversation_context_analys="",
                messages=[],
            )
            await self.update_conversation_status(
                conversation_id=payload_params.conversation_id,
                conversation_state=conversation_state,
            )

            return
        except (ClientResponseError, RedisError, OpenAIError) as e:
            stack = traceback.format_exc()
            full_exception_name = f"{type(e).__module__}.{type(e).__name__}"
            exception_message: str = str(e)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.user.created",
                params={
                    "conversation_id": payload_params.conversation_id,
                    "user_created_message": payload_params.clean_message,
                },
                stack_trace=stack
            )
            raise app_exception
        except Exception as ex:
            raise ex

    def _get_payload_params(self, payload: Dict) -> PayloadData:
        conversation_id: str = payload.get("data", {}).get("item", {}).get("id", "")
        user_data: Dict = payload.get("data", {}).get("item", {}).get("source", {})
        message: str = user_data.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        return PayloadData(conversation_id=conversation_id, clean_message=clean_message)
