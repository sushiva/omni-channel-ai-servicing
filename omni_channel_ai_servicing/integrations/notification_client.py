from .base_client import BaseServiceClient

class NotificationClient(BaseServiceClient):

    async def send_email(self, to: str, subject: str, body: str):
        payload = {"to": to, "subject": subject, "body": body}
        return await self._post("/notify/email", payload)
