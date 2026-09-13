from typing import Tuple, Optional
from ..tools.interfaces import GmailClient, StripeClient, SlackClient
from ..config import settings
from .gmail_live import LiveGmailClient
from .gmail_mock import MockGmailClient
from .stripe_live import LiveStripeClient
from .stripe_mock import MockStripeClient
from .slack_live import LiveSlackClient
from .slack_mock import MockSlackClient

def get_clients(
    mock_mode: Optional[bool] = None,
    scenario: Optional[str] = None
) -> Tuple[GmailClient, StripeClient, SlackClient]:
    """Factory creating Gmail, Stripe, and Slack clients based on mode and scenario."""
    # 1. Preset benchmark scenarios (scenario_1 to scenario_10) ALWAYS use mock clients
    if scenario and scenario.startswith("scenario_"):
        is_mock = True
    # 2. Explicit mock_mode override if provided
    elif mock_mode is not None:
        is_mock = mock_mode
    # 3. Fall back to environment configuration
    else:
        is_mock = settings.MOCK_MODE

    if is_mock:
        return (
            MockGmailClient(scenario=scenario),
            MockStripeClient(scenario=scenario),
            MockSlackClient(scenario=scenario)
        )
    else:
        # Live clients with fallback or safety validation
        return (
            LiveGmailClient(),
            LiveStripeClient(),
            LiveSlackClient()
        )

__all__ = [
    "get_clients",
    "LiveGmailClient",
    "MockGmailClient",
    "LiveStripeClient",
    "MockStripeClient",
    "LiveSlackClient",
    "MockSlackClient",
]
