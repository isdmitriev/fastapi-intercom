from dependency_injector import containers, providers
from services.mongodb_service import MongodbService
from services.redis_cache_service import RedisService
from services.web_hook_processor import WebHookProcessor
from services.intercom_api_service import IntercomAPIService
from services.openai_api_service import OpenAIService
from services.conversation_parts_service import ConversationPartsService
from services.redis_cache_service import MessagesCache
from services.openai_translator_service import OpenAITranslatorService
from services.es_service import ESService
from services.claude_ai import ClaudeService
from services.handlers.user_created_handler import UserCreatedHandler
from services.handlers.user_replied_handler import UserRepliedHandler
from services.handlers.admin_noted_handler import AdminNotedHandler
from services.handlers.messages_processor import MessagesProcessor
from services.handlers.admin_close_handler import AdminCloseHandler
from services.handlers.common import MessageHandler


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=['app', 'services'])
    # wiring_config = containers.WiringConfiguration(
    #     modules=[
    #         "app",
    #         "services.web_hook_processor",
    #         "services.redis_cache_service",
    #         "services.mongodb_service",
    #     ]
    # )

    mongo_db_service = providers.Singleton(MongodbService)
    redis_service = providers.Singleton(RedisService)
    es_service= providers.Singleton(ESService)
    intercom_api_service = providers.Singleton(IntercomAPIService)
    messages_cache_service = providers.Singleton(MessagesCache)
    open_ai_service = providers.Singleton(
        OpenAIService, messages_cache_service=messages_cache_service
    )
    claude_ai_service = providers.Singleton(
        ClaudeService, messages_cache_service=messages_cache_service
    )
    translations_service = providers.Singleton(OpenAITranslatorService)

    conversation_parts_service = providers.Singleton(
        ConversationPartsService,
        open_ai_client=open_ai_service,
        intercom_client=intercom_api_service,
    )

    web_hook_processor = providers.Singleton(
        WebHookProcessor,
        mongo_db_service=mongo_db_service,
        openai_service=open_ai_service,
        intercom_service=intercom_api_service,
        conversation_parts_service=conversation_parts_service,
        messages_cache_service=messages_cache_service,
        translations_service=translations_service,
        es_service=es_service,
        claude_ai_service=claude_ai_service,
    )
    user_created_service= providers.Singleton(
        UserCreatedHandler,
        intercom_api_service=intercom_api_service,
        open_ai_service=open_ai_service,
        messages_cache_service=messages_cache_service,
        translations_service=translations_service,
    )
    user_replied_service = providers.Singleton(
        UserRepliedHandler,
        intercom_api_service=intercom_api_service,
        open_ai_service=open_ai_service,
        messages_cache_service=messages_cache_service,
        translations_service=translations_service,
    )
    admin_noted_service = providers.Singleton(
        AdminNotedHandler,
        intercom_api_service=intercom_api_service,
        open_ai_service=open_ai_service,
        messages_cache_service=messages_cache_service,
        translations_service=translations_service,
    )
    admin_closed_service= providers.Singleton(
        AdminCloseHandler, messages_cache_service=messages_cache_service,
        intercom_api_service=intercom_api_service, open_ai_service=open_ai_service,
        translations_service=translations_service
    )

    messages_processor = providers.Singleton(
        MessagesProcessor,
        user_replied_service=user_replied_service,
        user_created_service=user_created_service,
        admin_noted_service=admin_noted_service,
        admin_closed_service=admin_closed_service,
        es_service=es_service,
    )
