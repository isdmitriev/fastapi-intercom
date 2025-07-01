from models.models import ConversationState
from services.redis_cache_service import MessagesCache
from dependency_injector.wiring import inject
from typing import Dict
from redis.exceptions import RedisError
from models.custom_exceptions import APPException
from services.handlers.common import MessageHandler


class AdminCloseHandler(MessageHandler):
    # @inject
    # def __init__(self, messages_cache_service: MessagesCache):
    #     self.messages_cache_service = messages_cache_service
    async def execute(self, payload: Dict):
        await self.admin_close_handler(payload=payload)

    async def admin_close_handler(self, payload: Dict):
        conversation_id: str = payload.get("data", {}).get("item", {}).get("id", "")
        try:
            await self.messages_cache_service.close_conversation(
                conversation_id=conversation_id
            )
        except RedisError as error:
            full_exception_name = f"{type(error).__module__}.{type(error).__name__}"
            exception_message: str = str(error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="conversation.admin.closed",
                params={"conversation_id": conversation_id},
            )
            raise app_exception
