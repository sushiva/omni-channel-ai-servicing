import httpx
from typing import Optional

class BaseServiceClient:
    def __init__(self, base_url: str, client: Optional[httpx.AsyncClient] = None):
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.AsyncClient(timeout=10.0)

    async def _post(self, path: str, json: dict):
        url = f"{self.base_url}{path}"
        response = await self.client.post(url, json=json)
        response.raise_for_status()
        return response.json()

    async def _get(self, path: str):
        url = f"{self.base_url}{path}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()
