from services.handlers.user_replied_handler import UserRepliedHandler
from services.handlers.user_created_handler import UserCreatedHandler
from services.handlers.admin_noted_handler import AdminNotedHandler
from dependency_injector.wiring import inject
from typing import Dict


class MessagesProcessor:
    @inject
    def __init__(
            self,
            user_created_service: UserCreatedHandler,
            user_replied_service: UserRepliedHandler,
            admin_noted_service: AdminNotedHandler,
    ):
        self.user_created_service = user_created_service
        self.user_replied_service = user_replied_service
        self.admin_noted_service = admin_noted_service

    async def process_message(self, payload: Dict):
        topic: str = payload.get('topic', '')
        if topic == 'conversation.user.created':
            await self.user_created_service.user_created_handler(payload=payload)
        if topic == 'conversation.user.replied':
            await self.user_replied_servie.user_replied_handler(payload=payload)
        if topic == 'conversation.admin.noted':
            await self.admin_noted_service.admin_noted_handler(payload=payload)
