from dependency_injector import containers, providers
from services.mongodb_service import MongodbService
from services.redis_cache_service import RedisService
from services.web_hook_processor import WebHookProcessor


class Container(containers.DeclarativeContainer):
    mongo_db_service: MongodbService = providers.Singleton(MongodbService)
    redis_service: RedisService = providers.Singleton(RedisService)
