from .base_client import BaseServiceClient

class CRMClient(BaseServiceClient):

    async def create_case(self, customer_id: str, intent: str, details: dict):
        payload = {
            "customer_id": customer_id,
            "intent": intent,
            "details": details
        }
        return await self._post("/crm/cases", payload)

    async def add_note(self, case_id: int, note: str):
        return await self._post(f"/crm/cases/{case_id}/notes", {"note": note})
