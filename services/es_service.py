from elasticsearch import Elasticsearch
from typing import Dict


class ESService:
    def __init__(self):
        self.client = Elasticsearch("http://localhost:9200")

    def create_index(self, index_name: str):
        self.client.indices.create(index=index_name)

    def delete_index(self, index_name: str):
        self.client.indices.delete(index=index_name)

    def add_document(self, index_name: str, document: Dict):
        result = self.client.index(index=index_name, document=document)
        return result
