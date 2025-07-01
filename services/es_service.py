from elasticsearch import Elasticsearch, AsyncElasticsearch
from typing import Dict
from dotenv import load_dotenv
import os
from services.handlers.processing_result import ProcessingResult
from models.custom_exceptions import APPException

load_dotenv()


class ESService:
    def __init__(self):
        self.client = Elasticsearch(os.getenv("ESEARCH_URI"))
        self.client_async = AsyncElasticsearch(os.getenv("ESEARCH_URI"))

    async def save_processing_result(self, processing_result: ProcessingResult):
        proces_result_dict: Dict = processing_result.model_dump()
        await self.client_async.index(
            index="processing_results", document=proces_result_dict
        )

    async def save_exception_async(self, app_exception: APPException):
        await self.client_async.index(index="errors", document=app_exception.__dict__)

    def create_index(self, index_name: str):
        self.client.indices.create(index=index_name)

    def delete_index(self, index_name: str):
        self.client.indices.delete(index=index_name)

    def add_document(self, index_name: str, document: Dict):
        result = self.client.index(index=index_name, document=document)
        return result
