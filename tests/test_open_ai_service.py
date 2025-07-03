import pytest
from di.di_container import Container
from services.openai_api_service import OpenAIService
from models.models import UserMessage
from services.handlers.models import MessageAnalysConfig
from services.handlers.analyze_message_service import MessageAnalyzeProcessor
from services.handlers.models import MessageAnalysResponse


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
# @pytest.mark.asyncio
# async def test_analyze_processor():
#     analyze_processor: MessageAnalyzeProcessor = Container.message_analyze_processor()
#     assert isinstance(analyze_processor, MessageAnalyzeProcessor)
#     analys_config: MessageAnalysConfig = MessageAnalysConfig(
#         message="good day!can i paint car?",
#         chat_context="",
#         model="gpt-3.5-turbo-0125",
#         type="fast",
#     )
#     analyze_result: MessageAnalysResponse = await analyze_processor.analyze_message(
#         analys_config=analys_config
#     )
#     assert isinstance(analyze_result,MessageAnalysResponse)
#     print(analyze_result.note_for_admin)
