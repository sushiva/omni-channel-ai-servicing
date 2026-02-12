import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from omni_channel_ai_servicing.app.config.settings import MOCK_SERVICES_BASE_URL
from omni_channel_ai_servicing.graph.registry import get_graph, get_initial_state
from omni_channel_ai_servicing.integrations.core_banking_client import CoreBankingClient
from omni_channel_ai_servicing.integrations.crm_client import CRMClient
from omni_channel_ai_servicing.integrations.notification_client import NotificationClient
from omni_channel_ai_servicing.monitoring.logger import get_logger

logger = get_logger("run_address_update")


async def main():
    logger.info("Starting address update workflow")

    core_client = CoreBankingClient(base_url=MOCK_SERVICES_BASE_URL)
    crm_client = CRMClient(base_url=MOCK_SERVICES_BASE_URL)
    notify_client = NotificationClient(base_url=MOCK_SERVICES_BASE_URL)

    graph = get_graph()
    state = get_initial_state(
        user_message="I want to change my address to 456 Oak Ave, Raleigh NC 27601",
        customer_id="cust123",
        core_client=core_client,
        crm_client=crm_client,
        notify_client=notify_client,
    )

    result = await graph.ainvoke(state)

    logger.info(
        "Workflow complete",
        extra={"extra": {
            "final_response": result.get("final_response"),
            "result": result.get("result"),
        }},
    )
    print("Final response:", result.get("final_response"))
    print("Result:", result.get("result"))


if __name__ == "__main__":
    asyncio.run(main())
