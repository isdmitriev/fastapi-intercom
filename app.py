from fastapi import FastAPI, Response, status, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict
import logging
import traceback
from services.redis_cache_service import RedisService
from services.mongodb_service import MongodbService
from services.es_service import ESService
from di.di_container import Container
from dependency_injector.wiring import inject, Provide
from models.custom_exceptions import APPException

import psutil
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_metricks.metricks import (
    APP_MEMORY_USAGE,
    SUCCESS_REQUEST_COUNT,
    FAILED_REQUEST_COUNT,
)
import os

from services.handlers.messages_processor import MessagesProcessor

container = Container()

container.wire(
    modules=[
        "app",

        "services.redis_cache_service",
        "services.mongodb_service",
        "services.es_service",
        "services.handlers.user_created_handler",
        "services.handlers.user_replied_handler",
        "services.handlers.admin_noted_handler",
        "services.handlers.messages_processor",
        "services.handlers.common",
    ]
)
app = FastAPI()

logger = logging.getLogger("main_app")
logger.setLevel(logging.INFO)
logger.propagate = False

handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

Instrumentator().instrument(app).expose(app)

process = psutil.Process()


@app.on_event("startup")
async def startup():
    container.init_resources()


@app.exception_handler(APPException)
async def handle_app_exception(
        request: Request,
        exception: APPException,
):
    es_service: ESService = container.es_service()

    await es_service.save_exception_async(app_exception=exception)

    logger.error(f"❌ error:{exception.message} event_type:{exception.event_type} ")
    FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).inc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exception.message},
    )


@app.exception_handler(Exception)
async def handle_common_exception(request: Request, exception: Exception):
    stack_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    logger.error(f"❌ {str(exception)} type:{type(exception)}")
    exception: APPException = APPException(
        message=str(exception),
        event_type="undefined",
        ex_class=type(exception).__name__,
        params={},
        stack_trace=stack_trace
    )
    await container.es_service().save_exception_async(app_exception=exception)
    FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).inc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=exception.message
    )


app.add_exception_handler(APPException, handle_app_exception)
app.add_exception_handler(Exception, handle_common_exception)


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


@app.post("/webhook/process/v2")
@inject
async def process_message(
        request: Request,
        redis_service: RedisService = Depends(lambda: container.redis_service()),
        messages_processor: MessagesProcessor = Depends(lambda: container.messages_processor())

):
    try:

        payload = await request.json()
        notification_event_id: str | None = payload.get("id", None)
        if notification_event_id == None:
            return Response(status_code=status.HTTP_200_OK)
        is_event_handled = await redis_service.set_key_async(notification_event_id, "1")
        if is_event_handled == True:
            await messages_processor.process_message(payload=payload)
            SUCCESS_REQUEST_COUNT.labels(
                pod_name=os.environ.get("HOSTNAME", "unknown")
            ).inc()

            return Response(
                status_code=status.HTTP_200_OK, content="message was processed"
            )
        else:
            SUCCESS_REQUEST_COUNT.labels(
                pod_name=os.environ.get("HOSTNAME", "unknown")
            ).inc()
            return Response(
                status_code=status.HTTP_200_OK, content="event already processed"
            )
    except ValueError as valError:
        logger.error("invalid json")

        FAILED_REQUEST_COUNT.labels(
            pod_name=os.environ.get("HOSTNAME", "unknown")
        ).inc()
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="invalid json"
        )

    except Exception as e:

        raise e

        # return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK, content="start app")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
