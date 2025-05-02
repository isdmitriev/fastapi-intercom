import requests
from typing import Dict, Tuple
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
import httpx
from httpx import Response

load_dotenv()


class IntercomAPIService:
    def __init__(self):
        self.access_token = os.getenv("INTERCOM_KEY_TEST")
        self.base_url = "https://api.intercom.io"

    def get_all_admins(self) -> Tuple[int, Dict | None]:
        url: str = self.base_url + "/admins"
        headers = {
            "Intercom-Version": "2.12",
            f"Authorization": f"Bearer {self.access_token}",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:

            return response.status_code, response.json()
        else:
            return response.status_code, None

    def create_admin(self, admin_email: str) -> Tuple[int, Dict | None]:
        url: str = self.base_url + "/admins"
        headers = {
            "Content-Type": "application/json",
            "Intercom-Version": "2.12",
            f"Authorization": f"Bearer {self.access_token}",
        }

        payload = {"email": admin_email, "role": "operator", "name": "ilya"}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.status_code, response.json()
        else:
            return response.status_code, None

    def create_conversation(
            self, user_id: str, message: str
    ) -> Tuple[int, Dict | None]:
        url: str = self.base_url + "/conversations"
        headers = {
            "Content-Type": "application/json",
            "Intercom-Version": "2.12",
            f"Authorization": f"Bearer {self.access_token}",
        }
        payload = {"from": {"type": "user", "id": user_id}, "body": message}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.status_code, response.json()
        else:
            return response.status_code, None

    def attach_admin_to_conversation(
            self, admin_id: str, conversation_id: str
    ) -> Tuple[int, Dict | None]:
        url = f"https://api.intercom.io/conversations/{conversation_id}/parts"
        headers = {
            "Content-Type": "application/json",
            "Intercom-Version": "2.12",
            "Accept": "application/json",
            f"Authorization": f"Bearer {self.access_token}",
        }
        payload = {
            "message_type": "assignment",
            "type": "admin",
            "admin_id": admin_id,
            "assignee_id": admin_id,
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.status_code, response.json()
        else:

            return response.status_code, None

    async def attach_admin_to_conversation_async(
            self, admin_id: str, conversation_id: str
    ) -> Tuple[int, Dict | None]:
        url = f"https://api.intercom.io/conversations/{conversation_id}/parts"
        headers = {
            "Content-Type": "application/json",
            "Intercom-Version": "2.12",
            "Accept": "application/json",
            f"Authorization": f"Bearer {self.access_token}",
        }
        payload = {
            "message_type": "assignment",
            "type": "admin",
            "admin_id": admin_id,
            "assignee_id": admin_id,
        }
        async with httpx.AsyncClient() as client:
            response: Response = client.post(url=url, headers=headers, json=payload)
            if response.status_code == 200:

                return response.status_code, response.json()
            else:
                return response.status_code, None

    def add_admin_note_to_conversation(
            self, conversation_id: str, admin_id: str, note: str
    ) -> Tuple[int, Dict | None]:
        url = f"https://api.intercom.io/conversations/{conversation_id}/reply"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "admin_id": admin_id,
            "type": "note",
            "message_type": "note",
            "body": note,
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.status_code, response.json()
        else:
            return response.status_code, None

    def add_admin_message_to_conversation(
            self, conversation_id: str, admin_id: str, message: str
    ) -> Tuple[int, Dict | None]:
        url = f"https://api.intercom.io/conversations/{conversation_id}/reply"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "admin_id": admin_id,
            "type": "note",
            "message_type": "comment",
            "body": message,
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.status_code, response.json()
        else:
            return response.status_code, None

    async def add_admin_message_to_conversation_async(
            self, conversation_id: str, admin_id: str, message: str
    ) -> Tuple[int, Dict | None]:
        url = f"https://api.intercom.io/conversations/{conversation_id}/reply"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "admin_id": admin_id,
            "type": "note",
            "message_type": "comment",
            "body": message,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return response.status, data
                else:
                    return response.status, None

    def create_user(self, email: str) -> Tuple[int, Dict | None]:
        url: str = self.base_url + "/contacts"
        headers = {
            "Content-Type": "application/json",
            "Intercom-Version": "2.12",
            f"Authorization": f"Bearer {self.access_token}",
        }
        payload = {"email": email}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.status_code, response.json()
        else:
            return response.status_code, None

    def get_all_users(self) -> Tuple[int, Dict | None]:
        url: str = self.base_url + "/contacts"
        headers = {
            "Intercom-Version": "2.12",
            "Authorization": f"Bearer {self.access_token}",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.status_code, response.json()
        else:
            return response.status_code, None

    def get_conversation_by_id(self, conversation_id: str) -> Tuple[int, Dict | None]:
        url: str = f"https://api.intercom.io/conversations/{conversation_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Intercom-Version": "2.12",
            "Accept": "application/json",
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.status_code, response.json()
            else:
                return response.status_code, None

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении информации о беседе: {e}")
            return 0, None

    async def add_user_replied_to_conversation(
            self, conversation_id: str, user_id: str, message: str
    ) -> Tuple[int, Dict | None]:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        payload = {
            "message_type": "comment",
            "body": message,
            "type": "user",
            "intercom_user_id": user_id,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.base_url}/conversations/{conversation_id}/reply",
                    headers=headers,
                    json=payload,
            ) as response:
                response.raise_for_status()
                if response.status == 200:
                    json = await response.json()
                    return response.status, json
                else:
                    return response.status, None

    async def add_admin_note_to_conversation_async(
            self, conversation_id: str, admin_id: str, note: str
    ) -> Tuple[int, Dict | None]:
        url = f"https://api.intercom.io/conversations/{conversation_id}/reply"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "admin_id": admin_id,
            "type": "note",
            "message_type": "note",
            "body": note,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return response.status, data
                else:
                    return response.status, None

    async def get_conversation_parts_by_id_async(
            self, conversation_id: str
    ) -> Tuple[int, Dict | None]:
        url: str = f"https://api.intercom.io/conversations/{conversation_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        query = {"display_as": "plaintext"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=query) as response:
                if response.status == 200:
                    data = await response.json()
                    return response.status, data
                else:
                    return response.status, None
