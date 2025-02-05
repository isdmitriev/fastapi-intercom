from celery_app import celery_app
from services.mongodb_service import MongodbService
import asyncio
import sys
import logging
from services.celery_tasks_service import CeleryTasksService
from typing import Dict

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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


@celery_app.task(name="mongodb_task_async")
def mongodb_task_async(message: Dict):
    asyncio.run(MongodbService().add_message_translated_dict(message))

    return f"Data Inserted"


@celery_app.task(name="translate_message_for_admin")
def translate_message_for_admin(message: str, admin_id: str, conversation_id: str):
    asyncio.run(
        CeleryTasksService().translate_message_from_hindi_to_admin(
            message, admin_id=admin_id, conversation_id=conversation_id
        )
    )
    return 'note send to admin'
