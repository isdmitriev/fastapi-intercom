from services.intercom_api_service import IntercomAPIService
from services.openai_api_service import OpenAIService
from services.openai_translator_service import OpenAITranslatorService
from services.redis_cache_service import MessagesCache
from dependency_injector.wiring import inject
from models.models import UserMessage, ConversationState
from services.handlers.models import MessageAnalysResponse, MessageAnalysConfig
from services.handlers.analyze_message_service import MessageAnalyzeService
from typing import Tuple, Dict
from enum import Enum
from abc import ABC, abstractmethod
from services.handlers.models import MessageAnalysConfig


class MessageStatus(Enum):
    NO_ERROR = "no_error"
    ERROR_FIXED = "error_fixed"
    UNCERTAIN = "uncertain"


class CommandLanguage(Enum):
    en = "English"
    hindi = "Hindi"
    hi = "Hinglish"
    bn = "Bengali"


class MessageHandler(ABC):
    @inject
    def __init__(
            self,
            intercom_api_service: IntercomAPIService,
            open_ai_service: OpenAIService,
            messages_cache_service: MessagesCache,
            translations_service: OpenAITranslatorService,
            message_analyze_service: MessageAnalyzeService,
    ):
        self.intercom_api_service = intercom_api_service
        self.open_ai_service = open_ai_service
        self.messages_cache_service = messages_cache_service
        self.translations_service = translations_service
        self.message_analyze_service = message_analyze_service

    @abstractmethod
    async def execute(self, payload: Dict):
        pass

    async def send_admin_reply_message(
            self,
            chat_context_analys: str,
            message: str,
            admin_id: str,
            conversation_id: str,
            target_lang: str,
    ) -> str | None:
        if target_lang == None:
            return None
        analys_config: MessageAnalysConfig = MessageAnalysConfig(
            message=message, chat_context=chat_context_analys,
            type='fast', model='gpt-3.5-turbo-0125'
        )
        if target_lang == CommandLanguage.hi.value:
            admin_note: str = (
                await self.translations_service.translate_message_from_english_to_hinglish_async_v2(
                    message=message
                )
            )
        elif target_lang == CommandLanguage.hindi.value:
            admin_note: str = (
                await self.translations_service.translate_message_from_english_to_hindi_async(
                    message=message
                )
            )
        elif target_lang == CommandLanguage.bn.value:
            admin_note: str = (
                await self.translations_service.translate_message_from_english_to_bengali_async(
                    message=message
                )
            )
        else:
            return
        await self.intercom_api_service.add_admin_message_to_conversation_async(
            conversation_id=conversation_id, message=admin_note, admin_id=admin_id
        )
        new_context_analys: str = (
            await self.message_analyze_service.analyze_agent_message(
                analys_config=analys_config
            )
        )
        return new_context_analys

    # async def get_note_for_admin(
    #         self, user_replied_message: str, current_context_analys: str
    # ) -> Tuple[str, str]:
    #
    #     analyzed_user_message: UserMessage = (
    #         await self.open_ai_service.analyze_message_with_correction_v4(
    #             message=user_replied_message, analys=current_context_analys
    #         )
    #     )
    #     if analyzed_user_message.status == MessageStatus.NO_ERROR.value:
    #         note_for_admin: str = (
    #                 "original:"
    #                 + user_replied_message
    #                 + "\n\n"
    #                 + analyzed_user_message.translated_text
    #         )
    #         return (note_for_admin, analyzed_user_message.context_analysis)
    #     if analyzed_user_message.status == MessageStatus.ERROR_FIXED.value:
    #         note_for_admin: str = (
    #                 "original:"
    #                 + user_replied_message
    #                 + "\n\n"
    #                 + analyzed_user_message.corrected_text
    #         )
    #         return (note_for_admin, analyzed_user_message.context_analysis)
    #     if analyzed_user_message.status == MessageStatus.UNCERTAIN.value:
    #         note: str = self.create_admin_note_for_uncertain_status(
    #             analyzed_message=analyzed_user_message
    #         )
    #         note_for_admin: str = (
    #                 "original:" + analyzed_user_message.original_text + "\n\n" + note
    #         )
    #         return (note_for_admin, analyzed_user_message.context_analysis)

    async def update_conversation_status(
            self, conversation_id: str, conversation_state: ConversationState
    ):
        await self.messages_cache_service.set_conversation_state(
            conversation_id=conversation_id, conversation_state=conversation_state
        )

    # def create_admin_note_for_uncertain_status(
    #         self, analyzed_message: UserMessage
    # ) -> str:
    #     possible_interpritations = analyzed_message.possible_interpretations
    #     one: str = possible_interpritations[0]
    #     two: str = possible_interpritations[1]
    #     note: str = (
    #             "translated: "
    #             + analyzed_message.translated_text
    #             + "\n"
    #             + analyzed_message.context_analysis
    #             + "\n"
    #             + one
    #             + "\n"
    #             + two
    #     )
    #     return note
