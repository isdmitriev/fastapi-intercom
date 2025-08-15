from fastapi import FastAPI, Response, status, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict
import logging
import traceback
from services.redis_cache_service import RedisService

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
logger = container.logger_service()
# logger = logging.getLogger("main_app")
# logger.setLevel(logging.INFO)
# logger.propagate = False
#
# handler = logging.StreamHandler()
# formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# logger.addHandler(handler)

Instrumentator().instrument(app).expose(app)

process = psutil.Process()


@app.on_event("startup")
async def startup():
    container.init_resources()


async def handle_app_exception(
        request: Request,
        exception: APPException,
):
    es_service: ESService = container.es_service()
    try:
        await es_service.save_exception_async(app_exception=exception)

        FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).inc()

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(exception)},
        )
    except Exception as e:

        FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).inc()

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)},
        )


async def handle_common_exception(request: Request, exception: Exception):
    stack_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

    app_exception: APPException = APPException(
        message=str(exception),
        event_type="unknown",
        ex_class=f"{type(exception).__module__}.{type(exception).__name__}",
        params={},
        service_name='unknown',
        stack_trace=stack_trace
    )
    logger.log_error(exception=app_exception)
    try:
        await container.es_service().save_exception_async(app_exception=exception)
        FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).inc()

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(exception)
        )
    except Exception as e:

        FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get("HOSTNAME", "unknown")).inc()

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e)
        )


app.add_exception_handler(APPException, handle_app_exception)
app.add_exception_handler(Exception, handle_common_exception)


@app.on_event("shutdown")
async def shutdown():
    interom_client = container.intercom_api_service()
    redis_client = container.redis_service()
    es_client = container.es_service()
    open_ai_client = container.open_ai_service()
    translator_service = container.translations_service()
    translator_service.close()
    await open_ai_client.close()
    await es_client.close_client()
    await redis_client.close()
    await interom_client.close_client_session()
    await container.shutdown_resources()


@app.middleware("http")
async def process_metrics(request: Request, call_next):
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

        FAILED_REQUEST_COUNT.labels(
            pod_name=os.environ.get("HOSTNAME", "unknown")
        ).inc()
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="invalid json"
        )


@app.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK, content="start app")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
