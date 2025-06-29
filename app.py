from fastapi import FastAPI, Response, status, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict
import logging
from services.web_hook_processor import WebHookProcessor
from services.redis_cache_service import RedisService
from services.mongodb_service import MongodbService
from services.es_service import ESService
from di.di_container import Container
from dependency_injector.wiring import inject
from models.custom_exceptions import APPException
from models.models import RequestInfo
from openai._exceptions import OpenAIError
from redis.exceptions import RedisError
from aiohttp.client_exceptions import ClientResponseError
import time
import psutil
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_metricks.metricks import (
    APP_MEMORY_USAGE,
    SUCCESS_REQUEST_COUNT,
    FAILED_REQUEST_COUNT,
    USER_CREATED_DURATION,
    ADMIN_NOTED_DURATION,
    USER_REPLIED_DURATION

)
import os
import canvas_handlers
from services.handlers.user_created_handler import UserCreatedHandler
from services.handlers.user_replied_handler import UserRepliedHandler
from services.handlers.admin_noted_handler import AdminNotedHandler
from services.handlers.admin_close_handler import AdminCloseHandler
from services.handlers.messages_processor import MessagesProcessor

container = Container()

container.wire(
    modules=[
        "app",
        "services.web_hook_processor",
        "services.redis_cache_service",
        "services.mongodb_service",
        "services.es_service",
        "services.handlers.user_created_handler",
        "services.handlers.user_replied_handler",
        "services.handlers.admin_noted_handler",
    ]
)
app = FastAPI()
app.include_router(canvas_handlers.router)
logger = logging.getLogger(__name__)

Instrumentator().instrument(app).expose(app)

process = psutil.Process()


@app.on_event("startup")
async def startup():
    container.init_resources()


@app.exception_handler(APPException)
@inject
async def handle_app_exception(
        request: Request,
        exception: APPException,
):
    es_service: ESService = container.es_service()

    es_service.add_document(index_name="errors", document=exception.__dict__)

    logger.error(f" error:{exception.message} event_type:{exception.event_type} ")
    FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get("HOSTNAME", "unknown"))

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exception.message},
    )


@app.exception_handler(Exception)
@inject
async def handle_common_exception(request: Request, exception: Exception):
    FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get("HOSTNAME", "unknown"))

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(exception)
    )


@app.on_event("shutdown")
async def shutdown():
    await container.shutdown_resources()


@app.middleware("http")
async def process_metrics(request: Request, call_next):
    # process = psutil.Process()

    memory_before = process.memory_info().rss / (1024 * 1024)

    response = await call_next(request)
    memory_after = process.memory_info().rss / (1024 * 1024)

    APP_MEMORY_USAGE.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).set(
        memory_after
    )

    return response


@app.post("/webhook/process")
@inject
async def get_message(
        request: Request,
        redis_service: RedisService = Depends(lambda: container.redis_service()),
        user_created_service: UserCreatedHandler = Depends(
            lambda: container.user_created_service()
        ),
        user_replied_servie: UserRepliedHandler = Depends(
            lambda: container.user_replied_service()
        ),
        admin_noted_service: AdminNotedHandler = Depends(
            lambda: container.admin_noted_service()
        ),
):
    try:
        payload: Dict = await request.json()
        notification_event_id: str | None = payload.get("id", None)
        if notification_event_id == None:
            return Response(status_code=status.HTTP_200_OK)
        is_event_handled = redis_service.set_key(notification_event_id, "1")
        if is_event_handled == True:

            topic: str = payload.get("topic", "")

            if topic == "conversation.user.created":
                start_time = time.time()
                await user_created_service.user_created_handler(payload=payload)
                USER_CREATED_DURATION.labels(
                    pod_name=os.environ.get("HOSTNAME", "unknown")
                ).observe(time.time() - start_time)
                SUCCESS_REQUEST_COUNT.labels(
                    pod_name=os.environ.get("HOSTNAME", "unknown")
                ).inc()
                return Response(status_code=status.HTTP_200_OK)
            if topic == "conversation.user.replied":
                start_time = time.time()
                await user_replied_servie.user_replied_handler(payload=payload)
                USER_REPLIED_DURATION.labels(
                    pod_name=os.environ.get("HOSTNAME", "unknown")
                ).observe(time.time() - start_time)

                SUCCESS_REQUEST_COUNT.labels(
                    pod_name=os.environ.get("HOSTNAME", "unknown")
                ).inc()
                return Response(status_code=status.HTTP_200_OK)
            if topic == "conversation.admin.noted":
                start_time = time.time()
                await admin_noted_service.admin_noted_handler(payload=payload)
                ADMIN_NOTED_DURATION.labels(
                    pod_name=os.environ.get("HOSTNAME", "unknown")
                ).observe(time.time() - start_time)

                SUCCESS_REQUEST_COUNT.labels(
                    pod_name=os.environ.get("HOSTNAME", "unknown")
                ).inc()
                return Response(status_code=status.HTTP_200_OK)
        else:
            SUCCESS_REQUEST_COUNT.labels(
                pod_name=os.environ.get("HOSTNAME", "unknown")
            ).inc()
            return Response(
                status_code=status.HTTP_200_OK, content="event already processed"
            )

    except ValueError as valError:

        FAILED_REQUEST_COUNT.labels(
            pod_name=os.environ.get("HOSTNAME", "unknown")
        ).inc()
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="invalid json"
        )

    except Exception as e:
        FAILED_REQUEST_COUNT.labels(
            pod_name=os.environ.get("HOSTNAME", "unknown")
        ).inc()

        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK, content="start app")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
