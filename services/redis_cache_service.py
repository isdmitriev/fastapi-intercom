from redis import Redis
import os
from dotenv import load_dotenv

load_dotenv()


class RedisService:
    def __init__(self):
        self.redis_client = Redis(host=os.getenv("REDIS_URI"), port=6379, db=1)

    def get_redis_client(self):
        return self.redis_client

    def set_key(self, key_name: str, key_value: str) -> bool:
        is_key_exist: bool = self.redis_client.setnx(key_name, key_value)
        return is_key_exist
