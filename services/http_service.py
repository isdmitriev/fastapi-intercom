import aiohttp

import asyncio
from typing import Dict, Any, Tuple
from models.custom_exceptions import APPException
import os
from dotenv import load_dotenv
from aiohttp.client_exceptions import ClientResponseError

load_dotenv()


class HTTPRequestService:
    def __init__(self):
        pass

    async def get_request_async(
        self, url: str, headers: Dict[str, Any]
    ) -> Tuple[int, Dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as response:
                if response.status == 200:
                    data: Dict = await response.json()
                    return response.status, data
                else:
                    raise await response.raise_for_status()

    async def post_request_async(
        self, url: str, headers: Dict[str, Any], payload: Dict[str, Any]
    ) -> Tuple[int, Dict]:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data: Dict = await response.json()
                    return response.status, data
                else:
                    raise await response.raise_for_status()


class IntercomAPIServiceV2:
    def __init__(self):
        self.http_service = HTTPRequestService()
        self.token = os.getenv("INTERCOM_KEY")

    async def add_admin_note_to_conversation_async(
        self, conversation_id: str, admin_id: str, note: str
    ):
        url: str = f"https://api.intercom.io/conversations/{conversation_id}/reply"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "admin_id": admin_id,
            "type": "note",
            "message_type": "note",
            "body": note,
        }
        try:
            response_data: Tuple[int, Dict] = (
                await self.http_service.post_request_async(
                    url=url, headers=headers, payload=payload
                )
            )
            return response_data
        except ClientResponseError as client_response_error:
            raise APPException(
                message="intercom api request exception,",
                event_type="conversation.admin.noted",
                ex_class="ClientResponseError",
                params={
                    "conversation_id": conversation_id,
                    "status_code": client_response_error.status,
                },
            )

        except Exception as e:

            raise e

    async def add_admin_message_to_conversation_async(
        self, conversation_id: str, admin_id: str, message: str
    ):
        url = f"https://api.intercom.io/conversations/{conversation_id}/reply"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "admin_id": admin_id,
            "type": "note",
            "message_type": "comment",
            "body": message,
        }
        try:
            response_data: Tuple[int, Dict] = (
                await self.http_service.post_request_async(
                    url=url, headers=headers, payload=payload
                )
            )
            return response_data
        except ClientResponseError as client_response_error:
            raise APPException(
                message="intercom api request exception,",
                event_type="conversation.admin.noted",
                ex_class="ClientResponseError",
                params={
                    "conversation_id": conversation_id,
                    "status_code": client_response_error.status,
                },
            )

        except Exception as e:
            full_exception_name = f"{type(e).__module__}.{type(e).__name__}"
            raise APPException(
                ex_class=full_exception_name,
                event_type="conversation.admin.noted",
                message=str(e),
                params={},
            )
