from typing import Dict
from services.mongodb_service import MongodbService
from services.openai_api_service import OpenAIService


class WebHookProcessor:

    def __init__(self):
        pass

    async def process_message(self, topic: str, message: Dict):

        if topic == "conversation.user.created":
            await self.handle_conversation_user_created(data=message)
            return

        elif topic == "conversation.user.replied":
            await self.handle_conversation_user_replied(data=message)
            return

        elif topic == "conversation.admin.replied":
            await self.handle_conversation_admin_replied(data=message)
            return

        elif topic == "conversation.admin.noted":
            await self.handle_conversation_admin_noted(data=message)
            return

        elif topic == "conversation.admin.assigned":
            await self.handle_conversation_admin_assigned(data=message)
            return
        else:
            return

    async def handle_conversation_user_created(self, data: Dict):
        print("conversation.user.created")

    async def handle_conversation_user_replied(self, data: Dict):
        user_reply: Dict = data['data']['item']['conversation_parts']['conversation_parts'][0]
        message: str = user_reply.get('body', '')
        user_email: str = user_reply.get('author', {}).get('email', '')
        user_id: str = user_reply.get('author', {}).get('id', '')
        print(f'{message}:{user_email}:{user_id}')
        print("conversation.user.replied")

    async def handle_conversation_admin_replied(self, data: Dict):
        print("conversation.admin.replied")

    async def handle_conversation_admin_noted(self, data: Dict):
        print("conversation.admin.noted")

    async def handle_conversation_admin_assigned(self, data: Dict):
        print("conversation.admin.assigned")
