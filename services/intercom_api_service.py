import requests
from typing import Dict, Tuple


class IntercomAPIService:
    def __init__(self):
        self.access_token = (
            "dG9rOmVlNGY1MzhmXzNjNjNfNGZjOF9hNmFkX2JmZDgyNmNlZWRlYzoxOjA="
        )
        self.base_url = "https://api.intercom.io/"

    def get_all_admins(self) -> Tuple[int, Dict | None]:
        url: str = self.base_url + "admins"
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
        url: str = self.base_url + "admins"
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
        url: str = self.base_url + "conversations"
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

    def create_user(self, email: str) -> Tuple[int, Dict | None]:
        url: str = self.base_url + "contacts"
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
        url: str = self.base_url + "contacts"
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
