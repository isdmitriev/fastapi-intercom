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
import aiohttp
import openai


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
        except APPException as app_ex:
            self.app_exception_handler(
                exception=app_ex,
                event_type="user_created",
                params={"user_created_message": payload_params.clean_message},
            )

        except Exception as ex:
            self.common_exception_handler(exception=ex, event_type="user_created")

    def _get_payload_params(self, payload: Dict) -> PayloadData:
        conversation_id: str = payload.get("data", {}).get("item", {}).get("id", "")
        user_data: Dict = payload.get("data", {}).get("item", {}).get("source", {})
        message: str = user_data.get("body", "")
        clean_message: str = BeautifulSoup(message, "html.parser").getText()
        return PayloadData(conversation_id=conversation_id, clean_message=clean_message)
