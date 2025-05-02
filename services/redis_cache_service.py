from redis import Redis, RedisError
import os
from dotenv import load_dotenv
from models.models import ConversationMessages
from models.custom_exceptions import APPException

load_dotenv()


class RedisService:
    def __init__(self):
        try:
            self.redis_client = Redis(
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


class MessagesCache:
    def __init__(self):
        try:
            self.redis_client = Redis(
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

    def set_key(self, key_name: str, key_value: str):
        self.redis_client.set(key_name, key_value, ex=21600)

    def set_conversation_messages(
        self, conversation_id: str, messages: ConversationMessages
    ):
        key_value: str = messages.model_dump_json()
        self.set_key(conversation_id, key_value)

    def get_conversation_messages(
        self, conversation_id: str
    ) -> ConversationMessages | None:
        value: str | None = self.redis_client.get(conversation_id)
        if value != None:
            result: ConversationMessages = ConversationMessages.model_validate_json(
                value
            )
            return result
        else:
            return None

    def delete_conversation(self, conversation_id: str):
        self.redis_client.delete(conversation_id)

    def set_conversation_language(self, conversation_id: str, language: str):
        self.set_key(conversation_id, language)

    def get_conversation_language(self, conversation_id: str):
        language: str = self.redis_client.get(conversation_id)
        return language

    def set_conversation_status(self, conversation_d: str, status: str):
        conv_status: str = "conv_status:" + conversation_d
        self.set_key(conv_status, status)

    def get_conversation_status(self, conversation_id: str) -> str | None:
        status: str = self.redis_client.get("conv_status:" + conversation_id)
        return status

    def close(self):
        self.redis_client.close()
