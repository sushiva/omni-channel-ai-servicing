from fastapi import APIRouter
from mock_services.models import EmailNotification

router = APIRouter()

@router.post("/email")
async def send_email(payload: EmailNotification):
    print(f"[EMAIL] To: {payload.to} | Subject: {payload.subject}")
    return {"status": "email sent"}
