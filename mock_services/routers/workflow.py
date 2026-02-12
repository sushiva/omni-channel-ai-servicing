import json

from fastapi import APIRouter, Depends, HTTPException
from mock_services.models import WorkflowStart, WorkflowCaseCreate
from mock_services.db import get_db

router = APIRouter()

@router.post("/start")
async def start_workflow(payload: WorkflowStart, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO workflows (type, payload, status) VALUES (?, ?, ?)",
        (payload.workflow_type, json.dumps(payload.payload), "PENDING")
    )
    await db.commit()
    return {"workflow_id": cursor.lastrowid, "status": "PENDING"}

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: int, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow": row}

@router.post("/case")
async def create_case(payload: WorkflowCaseCreate, db=Depends(get_db)):
    """Create a new case in the workflow management system"""
    cursor = await db.execute(
        "INSERT INTO workflows (type, payload, status) VALUES (?, ?, ?)",
        (payload.case_type, json.dumps({
            "description": payload.description,
            "priority": payload.priority,
            "metadata": payload.metadata
        }), "OPEN")
    )
    await db.commit()
    case_id = f"CASE-{cursor.lastrowid:06d}"
    return {
        "case_id": case_id,
        "status": "OPEN",
        "priority": payload.priority,
        "assigned_to": "customer_service_team"
    }
