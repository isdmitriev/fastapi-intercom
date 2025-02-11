from fastapi import FastAPI, Response, status, Request, Depends
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict
import motor.motor_asyncio
from services.web_hook_processor import WebHookProcessor
from services.mongodb_service import MongodbService
from di.di_container import Container
from dependency_injector.wiring import inject, Provide

container = Container()
app = FastAPI()
app.container = container
container.wire(modules=[__name__])


@app.post("/webhook/message")
@inject
async def get_message(
    request: Request,
    web_hook_processor: WebHookProcessor = Depends(
        Provide[Container.web_hook_processor]
    ),
    mongo_db_service: MongodbService = Depends(Provide[Container.mongo_db_service]),
):
    try:
        payload: Dict = await request.json()
        await mongo_db_service.add_document_to_collection(
            "intercom_app", "event_logs", payload
        )

        topic: str = payload.get("topic", "")
        await web_hook_processor.process_message(topic, payload)

        return Response(status_code=status.HTTP_200_OK)
    except:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK, content="start app")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
