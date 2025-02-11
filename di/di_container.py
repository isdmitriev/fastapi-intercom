from dependency_injector import containers, providers
from services.mongodb_service import MongodbService
from services.redis_cache_service import RedisService
from services.web_hook_processor import WebHookProcessor
from services.intercom_api_service import IntercomAPIService
from services.openai_api_service import OpenAIService
from services.conversation_parts_service import ConversationPartsService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=['app','services'])
    mongo_db_service = providers.Singleton(MongodbService)
    redis_service = providers.Singleton(RedisService)
    intercom_api_service = providers.Singleton(IntercomAPIService)
    open_ai_service = providers.Singleton(OpenAIService)

    conversation_parts_service = providers.Singleton(
        ConversationPartsService,
        open_ai_client=open_ai_service,
        intercom_client=intercom_api_service
    )

    web_hook_processor = providers.Singleton(
        WebHookProcessor,
        mongo_db_service=mongo_db_service,
        openai_service=open_ai_service,
        intercom_service=intercom_api_service,
        conversation_parts_service=conversation_parts_service,

    )
