import aiohttp
import asyncio
from typing import Dict, Any, Tuple
from models.custom_exceptions import IntercomAPIException


class HTTPRequestService:
    def __init__(self):
        pass

    async def get_request_async(
            self, url: str, headers: Dict[str, Any]
    ) -> Tuple[int, Dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as response:
                if (response.status == 200):
                    data: Dict = await response.json()
                    return response.status, data
                else:
                    raise await response.raise_for_status()

    async def post_request_async(
            self, url: str, headers: Dict[str, Any], payload: Dict[str, Any]
    ) -> Tuple[int, Dict]:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, json=payload) as response:
                if (response.status == 200):
                    data: Dict = await response.json()
                    return response.status, data
                else:
                    raise await response.raise_for_status()
