from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict
from models.models import MessageTranslated, User


class MongodbService:
    def __init__(self):
        self.client = AsyncIOMotorClient(
            "mongodb+srv://ily:asperger1988@cluster0.f5lev.mongodb.net/intercom_app?retryWrites=true&w=majority&appName=Cluster0"
        )

    async def add_document_to_collection(
        self, db_name: str, collection_name: str, document: Dict
    ):
        db = self.client.get_database(db_name)
        collection = db.get_collection(collection_name)
        await collection.insert_one(document)

    async def add_message_translated(self, message_translated: MessageTranslated):
        db = self.client.get_database("intercom_app")
        collection = db.get_collection("translations")
        await collection.insert_one(message_translated.dict())
