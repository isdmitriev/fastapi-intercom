from typing import Dict, Tuple

import os
from dotenv import load_dotenv

from aiohttp import ClientSession, ClientTimeout, TCPConnector, ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

load_dotenv()


class IntercomAPIService:
    def __init__(self):
        self.access_token = os.getenv("INTERCOM_KEY_TEST")
        self.base_url = "https://api.intercom.io"
        self.client_session: ClientSession | None = None

    async def _init_client_session(self):

        if self.client_session and not self.client_session.closed:
            return

        timeout: ClientTimeout = ClientTimeout(total=15)
        connector: TCPConnector = TCPConnector(
            limit=50, limit_per_host=30, ttl_dns_cache=300, use_dns_cache=True
        )
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.client_session = ClientSession(
            timeout=timeout, connector=connector, headers=headers
        )

    async def close_client_session(self):

        await self.client_session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(ClientError),
    )
    async def attach_admin_to_conversation_async(
            self, admin_id: str, conversation_id: str
    ) -> Tuple[int, Dict | None]:
        url = f"https://api.intercom.io/conversations/{conversation_id}/parts"
        if self.client_session is None:
            await self._init_client_session()

        payload = {
            "message_type": "assignment",
            "type": "admin",
            "admin_id": admin_id,
            "assignee_id": admin_id,
        }
        async with self.client_session.post(url=url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return response.status, data
            else:
                return response.status, None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(ClientError),
    )
    async def add_admin_message_to_conversation_async(
            self, conversation_id: str, admin_id: str, message: str
    ) -> Tuple[int, Dict | None]:
        url = f"https://api.intercom.io/conversations/{conversation_id}/reply"
        if self.client_session is None:
            await self._init_client_session()

        payload = {
            "admin_id": admin_id,
            "type": "note",
            "message_type": "comment",
            "body": message,
        }

        async with self.client_session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return response.status, data
            else:
                return response.status, None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(ClientError),
    )
    async def add_admin_note_to_conversation_async(
            self, conversation_id: str, admin_id: str, note: str
    ) -> Tuple[int, Dict | None]:
        url = f"https://api.intercom.io/conversations/{conversation_id}/reply"
        if self.client_session is None:
            await self._init_client_session()

        payload = {
            "admin_id": admin_id,
            "type": "note",
            "message_type": "note",
            "body": note,
        }

        async with self.client_session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return response.status, data
            else:
                return response.status, None
