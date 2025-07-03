from dependency_injector.wiring import inject
from services.handlers.models import MessageAnalysConfig, MessageAnalysResponse
from services.openai_api_service import OpenAIService
from models.models import UserMessage
from typing import Dict, Tuple
from enum import Enum
from abc import ABC, abstractmethod
from functools import cached_property


class MessageAnalyze(ABC):
    @inject
    def __init__(self, open_ai_service: OpenAIService):
        self.open_ai_service = open_ai_service

    @abstractmethod
    async def analyze_message(
        self, analys_config: MessageAnalysConfig
    ) -> MessageAnalysResponse:
        pass


class MessageStatus(Enum):
    NO_ERROR = "no_error"
    ERROR_FIXED = "error_fixed"
    UNCERTAIN = "uncertain"


class MessageAnalyzeService(MessageAnalyze):
    async def analyze_message(
        self, analys_config: MessageAnalysConfig
    ) -> MessageAnalysResponse:
        message_handlers: Dict = self._methods_dict
        analyzed_user_message: UserMessage = await message_handlers.get(
            analys_config.type
        )(analys_config=analys_config)

        note_for_admin, chat_context = self._get_note_for_admin(
            analyzed_user_message=analyzed_user_message
        )
        return MessageAnalysResponse(
            note_for_admin=note_for_admin, chat_context_analys=chat_context
        )

    async def analyze_agent_message(self, analys_config: MessageAnalysConfig) -> str:
        new_chat_context: str = (
            await self.open_ai_service.analyze_message_execute_agent(
                analys_config=analys_config
            )
        )
        return new_chat_context

    def _get_note_for_admin(
        self, analyzed_user_message: UserMessage
    ) -> Tuple[str, str]:
        if analyzed_user_message.status == MessageStatus.NO_ERROR.value:
            note_for_admin: str = (
                "original:"
                + analyzed_user_message.original_text
                + "\n\n"
                + analyzed_user_message.translated_text
            )
            return (note_for_admin, analyzed_user_message.context_analysis)
        if analyzed_user_message.status == MessageStatus.ERROR_FIXED.value:
            note_for_admin: str = (
                "original:"
                + analyzed_user_message.original_text
                + "\n\n"
                + analyzed_user_message.corrected_text
            )
            return (note_for_admin, analyzed_user_message.context_analysis)
        if analyzed_user_message.status == MessageStatus.UNCERTAIN.value:
            note: str = self.create_admin_note_for_uncertain_status(
                analyzed_message=analyzed_user_message
            )
            note_for_admin: str = (
                "original:" + analyzed_user_message.original_text + "\n\n" + note
            )
            return (note_for_admin, analyzed_user_message.context_analysis)
        pass

    def create_admin_note_for_uncertain_status(
        self, analyzed_message: UserMessage
    ) -> str:
        possible_interpritations = analyzed_message.possible_interpretations
        one: str = possible_interpritations[0]
        two: str = possible_interpritations[1]
        note: str = (
            "translated: "
            + analyzed_message.translated_text
            + "\n"
            + analyzed_message.context_analysis
            + "\n"
            + one
            + "\n"
            + two
        )
        return note

    @cached_property
    def _methods_dict(self):
        return {
            "fast": self.open_ai_service.analyze_message_execute_user,
            "power": self.open_ai_service.analyze_message_execute,
        }
