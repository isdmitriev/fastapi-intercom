from typing import Dict, Any, List


class ConversationPartsService:
    def __init__(self):
        pass

    def handle_conversation_parts(self, conversation_parts: Dict[str, Any]):
        parts: List[Dict] = conversation_parts.get("conversation_parts", {}).get(
            "conversation_parts", []
        )
        parts_reversed: List[Dict] = parts.reverse()
        for part in parts_reversed:
            body: str = part.get('body', '')
            part_type: str = part.get('part_type', '')
            author_type = part.get('author', {}).get('type', '')
            author_email: str = part.get('author', {}).get('email', '')
            author_name: str = part.get('author', {}).get('name', '')
            author_id: str = part.get('author', {}).get('id', '')
