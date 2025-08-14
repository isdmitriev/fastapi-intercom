import pytest
from unittest.mock import AsyncMock
from services.redis_cache_service import MessagesCache
from models.models import ConversationState
from models.custom_exceptions import APPException


@pytest.fixture
def mocked_conversation_state():
    mocked_conversation_state: ConversationState = ConversationState(
        conversation_id="123",
        conversation_status="stoped",
        conversation_language=None,
        conversation_last_message="good day",
        conversation_context_analys="",
        messages=[],
    )
    return mocked_conversation_state


@pytest.mark.asyncio
async def test_redis_error_decorator(mocked_conversation_state):
    messages_service: MessagesCache = MessagesCache()
    conversation_id: str = "123"
    with pytest.raises(APPException) as ex:
        await messages_service.set_conversation_state(
            conversation_id=conversation_id,
            conversation_state=mocked_conversation_state,
        )
    error = ex.value

    assert isinstance(error, APPException)
    assert error.params.get('conversation_id', '') == conversation_id
    assert error.params.get('conversation_state', '') == ''
    assert error.service_name == 'redis_set_state'
