from celery_app import celery_app
from services.mongodb_service import MongodbService
import asyncio
import sys
import logging
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

@celery_app.task(name="mongodb_task")
def mongodb_task(data):
    print(f"TASK STARTED: {data}")  # Явный print для проверки
    logger.debug("Debug message: %s", data)
    logger.info("Info message: %s", data)  # Попробуйте info уровень
    return f"Processed data: {data}"











