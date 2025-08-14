import pytest
from unittest.mock import AsyncMock

from services.openai_api_service import OpenAIService
from services.redis_cache_service import MessagesCache
from models.models import UserMessage
from services.handlers.models import MessageAnalysConfig
from typing import List, Dict
from services.handlers.models import MessageAnalysResponse
from models.custom_exceptions import APPException


@pytest.fixture
def mocked_open_ai_service():
    messages_cache: MessagesCache = MessagesCache()
    open_ai_service: OpenAIService = OpenAIService(
        messages_cache_service=messages_cache
    )
    open_ai_service.get_chat_history = AsyncMock(
        return_value=[{"role": "user", "content": "good day!"}]
    )
    return open_ai_service


@pytest.mark.asyncio
async def test_open_ai_service(mocked_open_ai_service):
    assert isinstance(mocked_open_ai_service, OpenAIService)
    history = await mocked_open_ai_service.get_chat_history(conversation_id="1")
    assert isinstance(history, List)
    analys_config: MessageAnalysConfig = MessageAnalysConfig(
        message="good day!", model="gpt-3.5-turbo-0125", type="fast", chat_context=""
    )
    result: UserMessage = await mocked_open_ai_service.analyze_message_execute_user(
        analys_config=analys_config
    )
    assert isinstance(result, UserMessage)


@pytest.mark.asyncio
async def test_openai_decorator(mocked_open_ai_service):
    analys_config: MessageAnalysConfig = MessageAnalysConfig(
        message="good day!", model="1gpt-3.5-turbo-0125", type="fast", chat_context=""
    )
    with pytest.raises(APPException) as ex:
        await mocked_open_ai_service.analyze_message_execute_user(
            analys_config=analys_config
        )
    error = ex.value

    assert isinstance(error, APPException)


# @pytest.mark.asyncio
# async def test_analyze_message_execute_user():
#     open_ai_service: OpenAIService = Container.open_ai_service()
#     assert isinstance(open_ai_service, OpenAIService)
#     analys_config: MessageAnalysConfig = MessageAnalysConfig(
#         message="good day! how to paint car?",
#         chat_context="",
#         model="gpt-3.5-turbo-0125",
#         type="fast",
#     )
#     result: UserMessage = await open_ai_service.analyze_message_execute_user(
#         analys_config=analys_config
#     )
#     print(result.context_analysis)
#     assert isinstance(result, UserMessage)
#
#
# @pytest.mark.asyncio
# async def test_analyze_message_execute_admin():
#     open_ai_service: OpenAIService = Container.open_ai_service()
#     assert isinstance(open_ai_service, OpenAIService)
#     analys_config: MessageAnalysConfig = MessageAnalysConfig(
#         message="good day!can i help you?",
#         chat_context="",
#         model="gpt-3.5-turbo-0125",
#         type="fast",
#     )
#     result: str = await open_ai_service.analyze_message_execute_agent(
#         analys_config=analys_config
#     )
#     print(result)
#     assert isinstance(result, str)
#
#
