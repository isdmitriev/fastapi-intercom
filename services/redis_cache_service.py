from redis import Redis
import os
from dotenv import load_dotenv
from models.models import ConversationMessages

load_dotenv()


class RedisService:
    def __init__(self):
        self.redis_client = Redis(host=os.getenv("REDIS_URI_KS"), decode_responses=True, port=6379, db=1)

    def get_redis_client(self):
        return self.redis_client

    def close(self):
        self.redis_client.close()

    def set_key(self, key_name: str, key_value: str) -> bool:
        is_key_exist: bool = self.redis_client.setnx(key_name, key_value)
        return is_key_exist


class MessagesCache:
    def __init__(self):
        self.redis_client = Redis(host=os.getenv("REDIS_URI_KS"), decode_responses=True, port=6379, db=2)

    def set_key(self, key_name: str, key_value: str):
        self.redis_client.set(key_name, key_value)

    def set_conversation_messages(
            self, conversation_id: str, messages: ConversationMessages
    ):
        key_value: str = messages.model_dump_json()
        self.set_key(conversation_id, key_value)

    def get_conversation_messages(
            self, conversation_id: str
    ) -> ConversationMessages | None:
        value: str = self.redis_client.get(conversation_id)
        result: ConversationMessages = ConversationMessages.model_validate_json(value)
        return result

    def delete_conversation(self, conversation_id: str):
        self.redis_client.delete(conversation_id)

    def close(self):
        self.redis_client.close()
