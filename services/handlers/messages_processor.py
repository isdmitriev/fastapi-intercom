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
from prometheus_client import Histogram, Counter, Gauge
from services.handlers.processing_result import ProcessingResult
from models.custom_exceptions import APPException
from prometheus_metricks.metricks import (
    USER_CREATED_DURATION,
    USER_REPLIED_DURATION,
    ADMIN_NOTED_DURATION,
)
import os

logger = logging.getLogger('message_processor')
logger.setLevel(logging.INFO)
logger.propagate = False

handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


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

                await self.user_created_service.execute(payload=payload)
                self._record_metric(USER_CREATED_DURATION, start_time=start_time)

            elif topic == InterestedEvents.user_replied.value:

                await self.user_replied_service.execute(payload=payload)
                self._record_metric(USER_REPLIED_DURATION, start_time=start_time)

            elif topic == InterestedEvents.admin_noted.value:

                await self.admin_noted_service.execute(payload=payload)
                self._record_metric(ADMIN_NOTED_DURATION, start_time=start_time)

            elif topic == InterestedEvents.admin_closed.value:
                await self.admin_closed_service.execute(payload=payload)
            execution_time: float = time.perf_counter() - start_time
            await self._logs_handler(topic=topic, execution_time=execution_time)
        except APPException as error:
            self._log_error(topic=topic, app_exception=error)
            raise error

        except Exception as e:
            self._log_error(app_exception=e, topic=topic)
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

    def _record_metric(self, metric: Histogram, start_time: float):
        metric.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).observe(
            time.perf_counter() - start_time
        )


    def _log_error(self, topic: str, app_exception: APPException | Exception):
        if isinstance(app_exception, APPException):
            logger.error(
                f"❌ Error while processing {topic}: {app_exception.message} type:{app_exception.ex_class}"
            )
        elif isinstance(app_exception, Exception):
            message: str = str(app_exception)
            logger.error(f"❌ Error while processing {topic}: {message}")
