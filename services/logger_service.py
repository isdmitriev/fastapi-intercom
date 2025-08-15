from abc import ABC, abstractmethod
import logging
import json
from typing import Dict
import datetime
from models.models import APPException
from pathlib import Path
import os
from services.handlers.processing_result import ProcessingResult
from pydantic import BaseModel


class JSONFromatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
        }
        log_data: Dict = {
            "message": record.getMessage(),
            "level": record.levelname,
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


class LoggerService:
    def __init__(self):
        self.json_logger: logging.Logger = self.init_json_logger()
        pass

    def init_json_logger(self) -> logging.Logger:
        logger_json = logging.getLogger("error_json_logger")
        logger_json.setLevel(logging.INFO)

        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(logging.INFO)
        json_formatter = JSONFromatter()
        stdout_handler.setFormatter(json_formatter)
        logger_json.addHandler(stdout_handler)
        logger_json.propagate = False
        return logger_json

    def log_error(self, exception: APPException):
        self.json_logger.error("❌ error", extra={"app_exception": exception.__dict__})

    def log_info(self, processing_result: ProcessingResult):
        self.json_logger.info(
            "✅ event was  hanndled",
            extra={"processing_result": processing_result.dict()},
        )

    def log_model(self, message: str, extra_name: str, model: BaseModel):
        self.json_logger.info(message, extra={extra_name: model.dict()})
