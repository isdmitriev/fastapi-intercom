import os
from openai import OpenAI, AsyncOpenAI, ChatCompletion, RateLimitError, APIError
from dotenv import load_dotenv
import json
from redis import RedisError
from typing import Dict, List
from models.models import UserMessage
from models.custom_exceptions import APPException

from services.redis_cache_service import MessagesCache
from models.models import ConversationMessages, ConversationMessage, ConversationState
from pydantic import BaseModel, ValidationError
from services.promt_storage import PromtStorage
from services.handlers.models import MessageAnalysConfig
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import tiktoken
from services.handlers.decorators import decorator_service

load_dotenv()


class OpenAIService:
    def __init__(self, messages_cache_service: MessagesCache):
        self.client_async = AsyncOpenAI(api_key=os.getenv("OPENAPI_KEY"))
        self.messages_cache_service = messages_cache_service

    async def _make_open_ai_request(
        self, message: str, model_name: str, system_promt: str, messages: List[Dict]
    ) -> UserMessage:
        try:

            request_response = await self._get_open_ai_response(
                message=message,
                model_name=model_name,
                system_promt=system_promt,
                messages=messages,
            )

            result_dict: Dict = json.loads(request_response)
            user_message: UserMessage = UserMessage.model_validate(result_dict)
            return user_message
        except ValidationError as validationError:
            raise validationError
        except Exception as error:
            raise error

    def get_count_request_tokens(
        self, messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo-0125"
    ) -> float:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:

            encoding = tiktoken.get_encoding("cl100k_base")

        num_tokens = 0

        for message in messages:

            num_tokens += 4

            for key, value in message.items():
                if isinstance(value, str):
                    num_tokens += len(encoding.encode(value))

                    if key == "name":
                        num_tokens -= 1

        num_tokens += 2
        return num_tokens

    # @retry(
    #     stop=stop_after_attempt(4),
    #     retry=retry_if_exception_type((APIError, RateLimitError)),
    #     wait=wait_exponential(multiplier=1, min=1, max=4),
    #     reraise=True,
    # )
    @decorator_service.service_exception_handler(
        ['system_promt','messages'],"open_ai_api_call", 3, RateLimitError, APIError, Exception
    )
    async def _get_open_ai_response(
        self, message: str, model_name: str, system_promt: str, messages: List[Dict]
    ) -> str:
        formatted_messages = [{"role": "system", "content": system_promt}]
        formatted_messages.extend(messages)
        formatted_messages.append({"role": "user", "content": message})
        request_response = await self.client_async.chat.completions.create(
            model=model_name,
            messages=formatted_messages,
            temperature=0,
            response_format={"type": "json_object"},
            timeout=20,
        )
        return request_response.choices[0].message.content

    async def analyze_message_execute(
        self, analys_config: MessageAnalysConfig
    ) -> UserMessage:
        chat_history: List[Dict] = await self.get_chat_history(
            conversation_id=analys_config.conversation_id
        )
        system_promt = PromtStorage.get_promt_analyze_message_execute()
        analyzed_result: UserMessage = await self._make_open_ai_request(
            message=analys_config.message,
            system_promt=system_promt,
            messages=chat_history,
            model_name=analys_config.model,
        )
        return analyzed_result

    async def analyze_message_execute_agent(
        self, analys_config: MessageAnalysConfig
    ) -> str:
        system_promt = PromtStorage.get_promt_analyze_message_execute_agent()
        if analys_config.chat_context == "":
            analys_config.chat_context = "No previous context available."
        agent_input = f"""## MESSAGE TYPE
        agent_message

        ## CURRENT MESSAGE
        "{analys_config.message}"

        ## CONTEXT ANALYSIS
        {analys_config.chat_context}"""

        updated_chat_context: Dict = json.loads(
            await self._get_open_ai_response(
                message=agent_input,
                model_name=analys_config.model,
                messages=[],
                system_promt=system_promt,
            )
        )
        context_analys_result: str = updated_chat_context.get("context_analysis", "")
        return context_analys_result

    async def analyze_message_execute_user(
        self, analys_config: MessageAnalysConfig
    ) -> UserMessage:
        system_promt = PromtStorage.get_promt_analyze_message_execute_user()
        if analys_config.chat_context == "":
            analys_config.chat_context = "No previous context available."

        user_input = f"""## MESSAGE TYPE
        user_message

        ## CURRENT MESSAGE
        "{analys_config.message}"

        ## CONTEXT ANALYSIS
        {analys_config.chat_context}"""

        analyzed_result: UserMessage = await self._make_open_ai_request(
            message=user_input,
            messages=[],
            model_name=analys_config.model,
            system_promt=system_promt,
        )
        return analyzed_result

    async def get_chat_history(self, conversation_id: str) -> List[Dict]:
        conversation_state: ConversationState = (
            await self.messages_cache_service.get_conversation_state(
                conversation_id=conversation_id
            )
        )
        if conversation_state is None:
            return []
        else:
            messages: List[ConversationMessage] = conversation_state.messages
            result_messages: List[Dict] = []
            for chat_message in messages:
                if chat_message.user.type == "admin":
                    result_messages.append(
                        {"role": "assistant", "content": chat_message.message}
                    )

                elif chat_message.user.type == "user":
                    result_messages.append(
                        {"role": "user", "content": chat_message.message}
                    )
            return result_messages

    async def close(self):
        if self.client_async is not None:
            await self.client_async.close()
