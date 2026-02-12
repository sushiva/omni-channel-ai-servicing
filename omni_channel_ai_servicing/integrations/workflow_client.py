from .base_client import BaseServiceClient

class WorkflowClient(BaseServiceClient):

    async def start_workflow(self, workflow_type: str, payload: dict):
        return await self._post(
            "/workflow/start",
            {"workflow_type": workflow_type, "payload": payload}
        )

    async def get_workflow(self, workflow_id: int):
        return await self._get(f"/workflow/{workflow_id}")

    async def create_case(
        self,
        case_type: str,
        description: str,
        priority: str = "medium",
        metadata: dict = None
    ):
        """Create a case in the workflow management system"""
        return await self._post(
            "/workflow/case",
            {
                "case_type": case_type,
                "description": description,
                "priority": priority,
                "metadata": metadata or {}
            }
        )
