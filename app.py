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
from prometheus_metricks.metricks import APP_MEMORY_USAGE, SUCCESS_REQUEST_COUNT, FAILED_REQUEST_COUNT
import os

container = Container()
container.init_resources()
container.wire(
    modules=[
        "app",
        "services.web_hook_processor",
        "services.redis_cache_service",
        "services.mongodb_service",
        "services.es_service",
    ]
)
app = FastAPI()
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
        # es_service: ESService = Depends(lambda: container.es_service()),
):
    es_service: ESService = container.es_service()
    request_info: RequestInfo = RequestInfo(
        exception=exception.__dict__,
        status="error",
        execution_time=None,
        event_type=exception.event_type,
    )
    es_service.add_document(index_name="requests", document=request_info.dict())
    logger.error(f" error:{exception.message} event_type:{exception.event_type} ")
    FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get('HOSTNAME', 'unknown'))

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exception.message},
    )


@app.exception_handler(OpenAIError)
@inject
async def handle_open_ai_exception(
        request: Request,
        openai_error: OpenAIError,
        es_service: ESService = Depends(lambda: container.es_service()),
):
    es_service: ESService = container.es_service()
    ex_class: str = type(openai_error).__module__ + "." + type(openai_error).__name__
    exception: APPException = APPException(
        message=str(openai_error), event_type="", ex_class=ex_class, params={}
    )
    request_info: RequestInfo = RequestInfo(
        exception=exception.__dict__, status="error", execution_time=None, event_type=""
    )
    es_service.add_document(index_name="requests", document=request_info.dict())
    logger.error(f" error:{exception.message} event_type:{exception.event_type} ")
    FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get('HOSTNAME', 'unknown')).inc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exception.message},
    )


@app.exception_handler(RedisError)
@inject
async def handle_redis_error(
        request: Request,
        error: RedisError,
        # es_service: ESService = Depends(lambda: container.es_service()),
):
    es_service: ESService = container.es_service()

    ex_class: str = type(error).__module__ + type(error).__name__
    exception: APPException = APPException(
        message=str(error), event_type="", ex_class=ex_class, params={}
    )
    request_info: RequestInfo = RequestInfo(
        exception=exception.__dict__, status="error", execution_time=None, event_type=""
    )
    es_service.add_document(index_name="requests", document=request_info.dict())
    logger.error(f" error:{exception.message} event_type:{exception.event_type} ")
    FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get('HOSTNAME', 'unknown')).inc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exception.message},
    )


@app.exception_handler(ClientResponseError)
@inject
async def handle_http_error(
        request: Request,
        error: ClientResponseError,
        es_service: ESService = Depends(lambda: container.es_service()),
):
    ex_class: str = type(error).__module__ + type(error).__name__
    exception: APPException = APPException(
        message=str(error), ex_class=ex_class, event_type="", params={}
    )
    request_info: RequestInfo = RequestInfo(
        exception=exception.__dict__, status="error", execution_time=None, event_type=""
    )
    es_service.add_document(index_name="requests", document=request_info.dict())
    logger.error(f" error:{exception.message} event_type:{exception.event_type} ")
    FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get('HOSTNAME', 'unknown')).inc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exception.message},
    )


# @app.exception_handler(Exception)
# async def handle_error(request: Request, exception: Exception):
#     FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get('HOSTNAME', 'unknown')).inc()
#
#     return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @app.on_event("startup")
# async def startup():
#     container.init_resources()


@app.on_event("shutdown")
async def shutdown():
    await container.shutdown_resources()


@app.middleware('http')
async def process_metrics(request: Request, call_next):
    # process = psutil.Process()

    memory_before = process.memory_info().rss / (1024 * 1024)

    response = await call_next(request)
    memory_after = process.memory_info().rss / (1024 * 1024)

    APP_MEMORY_USAGE.labels(pod_name=os.environ.get('HOSTNAME', 'unknown')).set(memory_after)

    return response


@app.post("/webhook/test")
@inject
async def get_message(
        request: Request,
        web_hook_processor: WebHookProcessor = Depends(
            lambda: container.web_hook_processor()
        ),
        mongo_db_service: MongodbService = Depends(lambda: container.mongo_db_service()),
        redis_service: RedisService = Depends(lambda: container.redis_service()),
):
    payload: Dict = await request.json()

    notification_event_id: str | None = payload.get("id", None)
    if notification_event_id == None:
        return Response(status_code=status.HTTP_200_OK)
    is_event_handled = redis_service.set_key(notification_event_id, "1")
    if is_event_handled == True:

        # await mongo_db_service.add_document_to_collection(
        #     "intercom_app", "event_logs", payload
        # )

        topic: str = payload.get("topic", "")
        await web_hook_processor.process_message(topic, payload)

        return Response(status_code=status.HTTP_200_OK)
    else:
        return Response(
            status_code=status.HTTP_200_OK, content="event already processed"
        )


@app.post("/webhook/message")
@inject
async def get_message(
        request: Request,
        web_hook_processor: WebHookProcessor = Depends(
            lambda: container.web_hook_processor()
        ),
        mongo_db_service: MongodbService = Depends(lambda: container.mongo_db_service()),
        redis_service: RedisService = Depends(lambda: container.redis_service()),
        es_service: ESService = Depends(lambda: container.es_service()),
):
    try:

        payload: Dict = await request.json()

        notification_event_id: str | None = payload.get("id", None)
        if notification_event_id == None:
            return Response(status_code=status.HTTP_200_OK)
        is_event_handled = redis_service.set_key(notification_event_id, "1")
        if is_event_handled == True:

            topic: str = payload.get("topic", "")
            await web_hook_processor.process_message(topic, payload)
            SUCCESS_REQUEST_COUNT.labels(pod_name=os.environ.get('HOSTNAME', 'unknown')).inc()

            return Response(status_code=status.HTTP_200_OK)
        else:
            SUCCESS_REQUEST_COUNT.labels(pod_name=os.environ.get('HOSTNAME', 'unknown')).inc()
            return Response(
                status_code=status.HTTP_200_OK, content="event already processed"
            )
    except ValueError as e:
        FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get('HOSTNAME', 'unknown')).inc()

        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Invalid JSON"
        )

    except Exception as ex:
        FAILED_REQUEST_COUNT.labels(pod_name=os.environ.get('HOSTNAME', 'unknown')).inc()

        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK, content="start app")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
