from celery import Celery

celery_app = Celery("worker",
                    broker="redis://localhost:6379/0",  # Используем Redis как брокер
                    backend="redis://localhost:6379/0",
                    include=['tasks'])
