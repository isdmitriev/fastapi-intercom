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
from services.logger_service import LoggerService
from prometheus_metricks.metricks import (
    USER_CREATED_DURATION,
    USER_REPLIED_DURATION,
    ADMIN_NOTED_DURATION,
)
import os


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
        logger_service: LoggerService,
    ):
        self.user_created_service = user_created_service
        self.user_replied_service = user_replied_service
        self.admin_noted_service = admin_noted_service
        self.admin_closed_service = admin_closed_service
        self.es_service = es_service
        self.logger_service = logger_service

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
            self._log_error(app_exception=error)
            raise error

    async def _logs_handler(self, topic: str, execution_time: float):

        if topic in [
            InterestedEvents.user_created.value,
            InterestedEvents.user_replied.value,
            InterestedEvents.admin_noted.value,
        ]:
            processing_result: ProcessingResult = ProcessingResult(
                is_success=True, event_type=topic, execution_time=execution_time
            )
            await self.es_service.save_processing_result(
                processing_result=processing_result
            )
            self.logger_service.log_info(processing_result=processing_result)

    def _record_metric(self, metric: Histogram, start_time: float):
        metric.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).observe(
            time.perf_counter() - start_time
        )

    def _log_error(self, app_exception: APPException):
        self.logger_service.log_error(exception=app_exception)
