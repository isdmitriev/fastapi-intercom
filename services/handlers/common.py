from services.intercom_api_service import IntercomAPIService
from services.openai_api_service import OpenAIService
from services.openai_translator_service import OpenAITranslatorService
from dependency_injector.wiring import inject
from models.models import UserMessage
from typing import Tuple, Dict
from enum import Enum


class MessageStatus(Enum):
    NO_ERROR = "no_error"
    ERROR_FIXED = "error_fixed"
    UNCERTAIN = "uncertain"


class CommonOperations:
    @inject
    def __init__(
            self,
            intercom_api_service: IntercomAPIService,
            translations_service: OpenAITranslatorService,
            open_ai_service: OpenAIService
    ):
        self.intercom_api_service = intercom_api_service
        self.open_ai_service = open_ai_service
        self.translations_service = translations_service

    async def send_admin_reply_message(self):
        pass

    async def get_note_for_admin(
            self, user_replied_message: str, current_context_analys: str
    ) -> Tuple[str, str]:

        analyzed_user_message: UserMessage = (
            await self.open_ai_service.analyze_message_with_correction_v4(
                message=user_replied_message, analys=current_context_analys
            )
        )
        if analyzed_user_message.status == MessageStatus.NO_ERROR.value:
            note_for_admin: str = (
                    "original:"
                    + user_replied_message
                    + "\n\n"
                    + analyzed_user_message.translated_text
            )
            return (note_for_admin, analyzed_user_message.context_analysis)
        if analyzed_user_message.status == MessageStatus.ERROR_FIXED.value:
            note_for_admin: str = (
                    "original:"
                    + user_replied_message
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
