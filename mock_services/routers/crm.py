import json

from fastapi import APIRouter, Depends
from mock_services.models import CaseCreate, Case
from mock_services.db import get_db

router = APIRouter()

@router.post("/cases")
async def create_case(case: CaseCreate, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO cases (customer_id, intent, details, status) VALUES (?, ?, ?, ?)",
        (case.customer_id, case.intent, json.dumps(case.details), "OPEN")
    )
    await db.commit()
    case_id = cursor.lastrowid
    return {"id": case_id, "status": "OPEN"}

@router.post("/cases/{case_id}/notes")
async def add_note(case_id: int, note: dict, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO case_notes (case_id, note) VALUES (?, ?)",
        (case_id, json.dumps(note))
    )
    await db.commit()
    return {"status": "note added"}
