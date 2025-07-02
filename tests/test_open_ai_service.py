import pytest
from di.di_container import Container
from services.openai_api_service import OpenAIService
from models.models import UserMessage

@pytest.mark.asyncio
async def test_analyze_message():
    open_ai_service:OpenAIService=Container.open_ai_service()
    assert isinstance(open_ai_service,OpenAIService)
    result:UserMessage=await open_ai_service.analyze_message_execute_user(message='good day!',current_chat_context='')
    print(result.status)
    assert isinstance(result,UserMessage)
