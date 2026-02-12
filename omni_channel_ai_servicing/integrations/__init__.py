from omni_channel_ai_servicing.app.config.settings import MOCK_SERVICES_BASE_URL
from omni_channel_ai_servicing.integrations.crm_client import CRMClient
from omni_channel_ai_servicing.integrations.core_banking_client import CoreBankingClient
from omni_channel_ai_servicing.integrations.notification_client import NotificationClient
from omni_channel_ai_servicing.integrations.workflow_client import WorkflowClient


def create_clients(base_url: str = MOCK_SERVICES_BASE_URL):
    return {
        "crm_client": CRMClient(base_url),
        "core_client": CoreBankingClient(base_url),
        "notify_client": NotificationClient(base_url),
        "workflow_client": WorkflowClient(base_url),
    }
