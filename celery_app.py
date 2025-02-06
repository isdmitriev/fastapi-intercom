from celery import Celery
from kombu import Queue

celery_app = Celery("worker",
                    broker="redis://redis:6379/0",  # Используем Redis как брокер
                    backend="redis://redis:6379/0",
                    include=['tasks'])
celery_app.conf.task_queues = (
    Queue('mongo_db'),
    Queue('admin_notes'),
)
