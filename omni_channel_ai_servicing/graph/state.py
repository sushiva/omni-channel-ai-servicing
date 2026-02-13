from typing import Optional, Dict, Any, List
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict

class AppState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
    
    # Trace
    trace_id: str = Field(default_factory=lambda: uuid4().hex[:8])

    # User input
    user_message: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None

    # Routing
    next: Optional[str] = None
    workflow_name: Optional[str] = None  # Which specialized workflow to execute
    channel: Optional[str] = None  # "email" | "chat" | "voice" | "mobile"

    # Workflow data
    customer_id: Optional[str] = None
    risk_tier: Optional[str] = None  # low | medium | high — populated by risk lookup
    customer_email: Optional[str] = None
    case_id: Optional[str] = None  # Changed to str to support CASE-XXXXXX format
    workflow_id: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    final_response: Optional[str] = None

    # Request metadata (channel-specific info, attachments, customer name, etc.)
    metadata: Optional[Dict[str, Any]] = None

    # RAG context
    retrieved_documents: Optional[List[Any]] = None
    context: Optional[str] = None
    context_metadata: Optional[Dict[str, Any]] = None

    # Integration clients
    crm_client: Any = None
    core_client: Any = None
    notify_client: Any = None
    workflow_client: Any = None
    
    llm: Any = None