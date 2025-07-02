from services.handlers.common import MessageAnalyze
from services.handlers.models import MessageAnalysConfig, MessageAnalysResponse
from services.openai_api_service import OpenAIService
from models.models import UserMessage
from typing import Dict


class MessageAnalyzeProcessor(MessageAnalyze):
    async def analyze_message(
        self, analys_config: MessageAnalysConfig
    ) -> MessageAnalysResponse:
        pass

    def _get_methods_dict(self):
        analyzed_methods = {
            "fast": self.open_ai_service.analyze_message_with_correction_v4,
            "slow": self.open_ai_service.analyze_message_with_correction_v3,
        }
        return analyzed_methods
