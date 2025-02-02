from fastapi import FastAPI, Response, status, Request
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict
import motor.motor_asyncio
from services.web_hook_processor import WebHookProcessor
from services.mongodb_service import MongodbService

app = FastAPI()

processor: WebHookProcessor = WebHookProcessor()
mongodb_service: MongodbService = MongodbService()


@app.post("/webhook/message")
async def get_message(request: Request):
    try:
        payload: Dict = await request.json()
        await mongodb_service.add_document_to_collection('intercom_app', 'event_logs', payload)

        topic: str = payload.get("topic", "")
        await processor.process_message(topic, payload)
        return Response(status_code=status.HTTP_200_OK)
    except:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK, content="start app kuber")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
