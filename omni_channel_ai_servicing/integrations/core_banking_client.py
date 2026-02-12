from .base_client import BaseServiceClient
from omni_channel_ai_servicing.monitoring.logger import get_logger

logger = get_logger("integrations.core")

class CoreBankingClient(BaseServiceClient):

    async def update_address(self, customer_id: str, address: dict):
        logger.info(
            "Updating address",
            extra={"extra": {"customer_id": customer_id, "address": address}},
        )
        resp = await self._post(
            f"/core/customers/{customer_id}/address",
            {"address": address},
        )
        logger.info(
            "Updated address response",
            extra={"extra": {"customer_id": customer_id, "response": resp}},
        )
        return resp
