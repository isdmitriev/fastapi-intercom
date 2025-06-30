from services.handlers.user_replied_handler import UserRepliedHandler
from services.handlers.user_created_handler import UserCreatedHandler
from services.handlers.admin_noted_handler import AdminNotedHandler
from services.handlers.admin_close_handler import AdminCloseHandler
from dependency_injector.wiring import inject
from typing import Dict
from services.es_service import ESService
import logging
import time
from enum import Enum
from services.handlers.processing_result import ProcessingResult
from models.custom_exceptions import APPException
from prometheus_metricks.metricks import (
    USER_CREATED_DURATION,
    USER_REPLIED_DURATION,
    ADMIN_NOTED_DURATION,
)
import os

logging.basicConfig(level=logging.DEBUG, )
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class InterestedEvents(Enum):
    user_created = "conversation.user.created"
    user_replied = "conversation.user.replied"
    admin_noted = "conversation.admin.noted"
    admin_closed = "conversation.admin.closed"


class MessagesProcessor:
    @inject
    def __init__(
            self,
            user_created_service: UserCreatedHandler,
            user_replied_service: UserRepliedHandler,
            admin_noted_service: AdminNotedHandler,
            admin_closed_service: AdminCloseHandler,
            es_service: ESService,
    ):
        self.user_created_service = user_created_service
        self.user_replied_service = user_replied_service
        self.admin_noted_service = admin_noted_service
        self.admin_closed_service = admin_closed_service
        self.es_service = es_service

    async def process_message(self, payload: Dict):
        try:
            start_time = time.perf_counter()
            topic: str = payload.get("topic", "")
            if topic == InterestedEvents.user_created.value:
                start_time = time.perf_counter()
                await self.user_created_service.user_created_handler(payload=payload)

                USER_CREATED_DURATION.labels(
                    pod_name=os.environ.get("HOSTNAME", "unknown")
                ).observe(time.perf_counter() - start_time)

            elif topic == InterestedEvents.user_replied.value:
                replied_start = time.perf_counter()
                await self.user_replied_service.user_replied_handler(payload=payload)
                USER_REPLIED_DURATION.labels(
                    pod_name=os.environ.get("HOSTNAME", "unknown")
                ).observe(time.perf_counter() - replied_start)
            elif topic == InterestedEvents.admin_noted.value:
                admin_note_start = time.perf_counter()
                await self.admin_noted_service.admin_noted_handler(payload=payload)
                ADMIN_NOTED_DURATION.labels(
                    pod_name=os.environ.get("HOSTNAME", "unknown")
                ).observe(time.perf_counter() - admin_note_start)
            elif topic == InterestedEvents.admin_closed.value:
                await self.admin_closed_service.admin_close_handler(payload=payload)
            execution_time: float = time.perf_counter() - start_time
            await self._logs_handler(topic=topic, execution_time=execution_time)
        except APPException as error:
            logger.exception(f"❌ Error while processing {topic}: {str(error)}")
            await self.es_service.save_excepton_async(app_exception=error)
            return
        except Exception as e:
            logger.exception(f"❌ Error while processing {topic}: {str(e)}")
            raise e

    async def _logs_handler(self, topic: str, execution_time: float):

        if topic in [
            InterestedEvents.user_created.value,
            InterestedEvents.user_replied.value,
            InterestedEvents.admin_noted.value,
        ]:
            logger.info(f"✅ {topic} event processed  processing time:{execution_time}")
            processing_result: ProcessingResult = ProcessingResult(
                is_success=True, event_type=topic, execution_time=execution_time
            )
            await self.es_service.save_processing_result(
                processing_result=processing_result
            )
        else:
            logger.warning(f"Received unknown topic: {topic}")
