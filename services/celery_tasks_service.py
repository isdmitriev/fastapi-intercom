from services.openai_api_service import OpenAIService
from services.intercom_api_service import IntercomAPIService
from services.conversation_parts_service import ConversationPartsService


class CeleryTasksService:
    def __init__(self):
        self.open_ai_client = OpenAIService()
        self.intercom_client = IntercomAPIService()
        self.conversation_parts_service = ConversationPartsService()

    async def translate_message_from_hindi_to_admin(
        self, message: str, admin_id: str, conversation_id: str
    ):
        message_en: str = (
            await self.open_ai_client.translate_message_from_hindi_to_english_async(
                message
            )
        )
        response = await self.intercom_client.add_admin_note_to_conversation_async(
            conversation_id=conversation_id, admin_id=admin_id, note=message_en
        )

    async def translate_message_from_bengali_to_admin(
        self, message: str, conversation_id: str, admin_id: str
    ):
        message_en: str = (
            await self.open_ai_client.translate_message_from_bengali_to_english_async(
                message=message
            )
        )
        response = await self.intercom_client.add_admin_note_to_conversation_async(
            note=message_en, conversation_id=conversation_id, admin_id=admin_id
        )

    async def handle_admin_note(
        self, conversation_id: str, admin_id: str, admin_note: str
    ):
        await self.conversation_parts_service.handle_admin_note(
            conversation_id=conversation_id, admin_id=admin_id, admin_note=admin_note
        )
