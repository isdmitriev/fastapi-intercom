from fastapi import FastAPI, Response, status, Request, Depends
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict
import logging
from services.web_hook_processor import WebHookProcessor
from services.redis_cache_service import RedisService
from services.mongodb_service import MongodbService
from di.di_container import Container
from dependency_injector.wiring import inject

container = Container()
container.init_resources()
container.wire(
    modules=[
        "app",
        "services.web_hook_processor",
        "services.redis_cache_service",
        "services.mongodb_service",
    ]
)
app = FastAPI()
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    container.init_resources()


@app.on_event("shutdown")
async def shutdown():
    await container.shutdown_resources()


@app.post("/webhook/message")
@inject
async def get_message(
        request: Request,
        web_hook_processor: WebHookProcessor = Depends(
            lambda: container.web_hook_processor()
        ),
        mongo_db_service: MongodbService = Depends(lambda: container.mongo_db_service()),
        redis_service: RedisService = Depends(lambda: container.redis_service()),
):
    try:
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
    except ValueError as e:

        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid JSON")

    except:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK, content="start app")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
