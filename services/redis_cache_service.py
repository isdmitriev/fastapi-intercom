from redis import Redis, RedisError
import os
from dotenv import load_dotenv
from models.models import ConversationMessages, ConversationState
from models.custom_exceptions import APPException
from services.handlers.decorators import decorator_service
from redis.asyncio import Redis as RedisAsync, ConnectionPool
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

load_dotenv()


class RedisService:
    def __init__(self):
        try:

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

    async def close(self):
        await self.redis_client_async.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type(RedisError),
    )
    async def set_key_async(self, key_name: str, key_value: str) -> bool:
        is_key_exist: bool = await self.redis_client_async.setnx(key_name, key_value)
        return is_key_exist


class MessagesCache:
    def __init__(self):
        try:

            self.redis_client_async = RedisAsync(
                host=os.getenv("REDIS_URI"),
                decode_responses=True,
                port=6379,
                db=2,
                max_connections=20,
            )
        except RedisError as redis_error:
            full_exception_name = (
                f"{type(redis_error).__module__}.{type(redis_error).__name__}"
            )
            exception_message: str = str(redis_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="unknown",
                service_name='redis_init',
                params={},
            )
            self.redis_client_async = None
            raise app_exception
        except Exception as e:
            self.redis_client_async = None
            raise e

    # @retry(
    #     stop=stop_after_attempt(3),
    #     wait=wait_exponential(multiplier=1, min=1, max=10),
    #     retry=retry_if_exception_type(RedisError),
    # )
    @decorator_service.service_exception_handler('redis_set_state', 3, RedisError, Exception)
    async def set_conversation_state(
            self, conversation_id: str, conversation_state: ConversationState
    ):
        key: str = f"conversation_state:{conversation_id}"
        value: str = conversation_state.model_dump_json()
        await self.redis_client_async.set(key, value, ex=1600)

    async def close_conversation(self, conversation_id: str):
        key: str = f"conversation_state:{conversation_id}"
        await self.redis_client_async.delete(key)

    # @retry(
    #     stop=stop_after_attempt(3),
    #     wait=wait_exponential(multiplier=1, min=1, max=10),
    #     retry=retry_if_exception_type(RedisError),
    # )
    @decorator_service.service_exception_handler('redis_get_state', 3, RedisError, Exception)
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
        if (self.redis_client_async is not None):
            await self.redis_client_async.close()
