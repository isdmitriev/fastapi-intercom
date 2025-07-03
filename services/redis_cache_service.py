from redis import Redis, RedisError
import os
from dotenv import load_dotenv
from models.models import ConversationMessages, ConversationState
from models.custom_exceptions import APPException
from models.models import ConversationContext
from redis.asyncio import Redis as RedisAsync

load_dotenv()


class RedisService:
    def __init__(self):
        try:
            self.redis_client = Redis(
                host=os.getenv("REDIS_URI"), decode_responses=True, port=6379, db=1
            )
            self.redis_client_async = RedisAsync(
                host=os.getenv("REDIS_URI"), decode_responses=True, port=6379, db=1
            )
        except RedisError as redis_error:
            full_exception_name = (
                f"{type(redis_error).__module__}.{type(redis_error).__name__}"
            )
            exception_message: str = str(redis_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="MessagesCache_Init",
                params={},
            )
            raise app_exception
        except Exception as e:
            raise e

    def get_redis_client(self):
        return self.redis_client

    def close(self):
        self.redis_client.close()

    def set_key(self, key_name: str, key_value: str) -> bool:
        is_key_exist: bool = self.redis_client.setnx(key_name, key_value)
        return is_key_exist

    async def set_key_async(self, key_name: str, key_value: str) -> bool:
        is_key_exist: bool = await self.redis_client_async.setnx(key_name, key_value)
        return is_key_exist


class MessagesCache:
    def __init__(self):
        try:

            self.redis_client_async = RedisAsync(
                host=os.getenv("REDIS_URI"), decode_responses=True, port=6379, db=2
            )
        except RedisError as redis_error:
            full_exception_name = (
                f"{type(redis_error).__module__}.{type(redis_error).__name__}"
            )
            exception_message: str = str(redis_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="MessagesCache_Init",
                params={},
            )
            raise app_exception
        except Exception as e:
            raise e

    async def set_conversation_state(
            self, conversation_id: str, conversation_state: ConversationState
    ):
        key: str = f"conversation_state:{conversation_id}"
        value: str = conversation_state.model_dump_json()
        await self.redis_client_async.set(key, value, ex=1600)

    async def close_conversation(self, conversation_id: str):
        key: str = f"conversation_state:{conversation_id}"
        await self.redis_client_async.delete(key)

    async def get_conversation_state(
            self, conversation_id: str
    ) -> ConversationState | None:
        value: str | None = await self.redis_client_async.get(
            f"conversation_state:{conversation_id}"
        )
        if value is not None:
            state: ConversationState = ConversationState.model_validate_json(value)
            return state
        else:
            return None

    async def close_async(self):
        await self.redis_client_async.close()
