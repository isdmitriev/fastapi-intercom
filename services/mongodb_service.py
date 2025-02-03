from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict
from models.models import MessageTranslated, User
import os
from dotenv import load_dotenv

load_dotenv()


class MongodbService:
    def __init__(self):
        self.client = AsyncIOMotorClient(
            os.getenv('MONGODB_URI')

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
