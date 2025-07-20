from elasticsearch import Elasticsearch, AsyncElasticsearch
from typing import Dict
from dotenv import load_dotenv
import os
from services.handlers.processing_result import ProcessingResult
from models.custom_exceptions import APPException
from elasticsearch.exceptions import TransportError

load_dotenv()
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class ESService:
    def __init__(self):
        self.client_async = AsyncElasticsearch(
            os.getenv("ESEARCH_URI"), request_timeout=10
        )

    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(TransportError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def save_processing_result(self, processing_result: ProcessingResult):
        proces_result_dict: Dict = processing_result.model_dump()
        await self.client_async.index(
            index="processing_results", document=proces_result_dict
        )

    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(TransportError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def save_exception_async(self, app_exception: APPException):
        await self.client_async.index(index="errors", document=app_exception.__dict__)

    async def close_client(self):
        await self.client_async.close()
