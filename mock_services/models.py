from pydantic import BaseModel
from typing import Optional, Dict

class CaseCreate(BaseModel):
    customer_id: str
    intent: str
    details: Dict

class Case(BaseModel):
    id: int
    customer_id: str
    intent: str
    details: Dict
    status: str = "OPEN"

class WorkflowCaseCreate(BaseModel):
    case_type: str
    description: str
    priority: str = "medium"
    metadata: Dict = {}

class AddressUpdate(BaseModel):
    address: Dict

class EmailNotification(BaseModel):
    to: str
    subject: str
    body: str

class WorkflowStart(BaseModel):
    workflow_type: str
    payload: Dict
