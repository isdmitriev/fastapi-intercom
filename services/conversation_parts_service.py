from typing import Dict, Any, List
from services.openai_api_service import OpenAIService
from services.intercom_api_service import IntercomAPIService
from typing import Dict
from bs4 import BeautifulSoup


class ConversationPartsService:
    def __init__(self):
        self.open_ai_client = OpenAIService()
        self.intercom_client = IntercomAPIService()

    async def handle_conversation_parts_async(
            self,
            conversation_id: str,
            admin_id: str,
            admin_message: str,
            conversation_parts: Dict[str, Any],
    ):
        parts: List[Dict] = conversation_parts.get("conversation_parts", {}).get(
            "conversation_parts", []
        )
        is_reply_for_first_message = True

        parts_reversed: List[Dict] = list(reversed(parts))

        for part in parts_reversed:
            body: str = part.get("body", "")
            part_type: str = part.get("part_type", "")
            author_type = part.get("author", {}).get("type", "")
            author_email: str = part.get("author", {}).get("email", "")
            author_name: str = part.get("author", {}).get("name", "")
            author_id: str = part.get("author", {}).get("id", "")
            if author_type == "user" and part_type == "comment":
                is_reply_for_first_message = False
                message_language: str = await self.open_ai_client.detect_language_async(
                    body
                )
                if message_language == "hi":
                    admin_reply_message = await self.open_ai_client.translate_message_from_english_to_hindi_async(
                        message=admin_message
                    )
                    await self.intercom_client.add_admin_message_to_conversation_async(
                        message=admin_reply_message,
                        conversation_id=conversation_id,
                        admin_id=admin_id,
                    )

                elif message_language == "bn":

                    admin_reply_message = await self.open_ai_client.translate_message_from_english_to_bengali_async(
                        message=admin_message
                    )
                    await self.intercom_client.add_admin_message_to_conversation_async(
                        message=admin_reply_message,
                        conversation_id=conversation_id,
                        admin_id=admin_id,
                    )

                else:
                    return
        if is_reply_for_first_message == True:
            first_user_message: str = conversation_parts.get("source", {}).get(
                "body", ""
            )
            clean_message: str = BeautifulSoup(
                first_user_message, "html.parser"
            ).getText()
            first_user_message_language_code: str = (
                await self.open_ai_client.detect_language_async(clean_message)
            )
            if first_user_message_language_code == "hi":
                admin_reply_message = await self.open_ai_client.translate_message_from_english_to_hindi_async(
                    message=admin_message
                )
                await self.intercom_client.add_admin_message_to_conversation_async(
                    conversation_id=conversation_id,
                    admin_id=admin_id,
                    message=admin_reply_message,
                )
            else:
                return


    async def handle_admin_note(
            self, conversation_id: str, admin_id: str, admin_note: str
    ):
        status_code, conversation_parts = (
            await self.intercom_client.get_conversation_parts_by_id_async(
                conversation_id=conversation_id
            )
        )

        await self.handle_conversation_parts_async(
            conversation_id=conversation_id,
            conversation_parts=conversation_parts,
            admin_id=admin_id,
            admin_message=admin_note,
        )
