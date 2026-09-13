from typing import Dict, Any, List, Optional
import os
from .base import ActionType, ToolDefinition, AppCategory, AppMetadata
from ..config import settings

# Predefined App Catalogue
APPS_CATALOGUE: Dict[str, AppMetadata] = {
    "gmail": AppMetadata(
        app_id="gmail",
        name="Gmail",
        category=AppCategory.COMMUNICATION,
        description="Search threads, read incoming messages, send notification and follow-up emails.",
        icon="mail",
        status="connected" if (os.path.exists(settings.GMAIL_TOKEN_PATH) or os.path.exists(settings.GMAIL_CREDENTIALS_PATH)) else "available",
        supported_events=["new_email", "label_added", "thread_replied"],
        available_actions=["search_messages", "read_threads", "send_email"]
    ),
    "stripe": AppMetadata(
        app_id="stripe",
        name="Stripe (Test Mode)",
        category=AppCategory.PAYMENTS,
        description="Query payment intents, search customer charges, and execute verified refunds in TEST mode.",
        icon="credit-card",
        status="connected" if settings.STRIPE_SECRET_KEY else "available",
        supported_events=["charge_created", "charge_disputed", "refund_created"],
        available_actions=["search_charges", "get_customer", "create_refund"]
    ),
    "slack": AppMetadata(
        app_id="slack",
        name="Slack",
        category=AppCategory.COMMUNICATION,
        description="Search internal channels for customer context and post real-time agent alerts and status dossiers.",
        icon="message-square",
        status="connected" if settings.SLACK_BOT_TOKEN else "available",
        supported_events=["message_posted", "mention", "reaction_added"],
        available_actions=["search_messages", "post_message", "list_channels"]
    ),
    "github": AppMetadata(
        app_id="github",
        name="GitHub",
        category=AppCategory.DEVELOPER,
        description="Monitor repositories, extract issue context, dispatch workflow triggers.",
        icon="code",
        status="coming_soon",
        supported_events=["issue_opened", "pull_request", "release_created"],
        available_actions=["create_issue", "read_pull_request", "dispatch_workflow"]
    ),
    "google_calendar": AppMetadata(
        app_id="google_calendar",
        name="Google Calendar",
        category=AppCategory.PRODUCTIVITY,
        description="Schedule meetings, detect interview slots, check team availability.",
        icon="calendar",
        status="coming_soon",
        supported_events=["event_created", "event_updated"],
        available_actions=["create_event", "list_events"]
    ),
    "google_drive": AppMetadata(
        app_id="google_drive",
        name="Google Drive",
        category=AppCategory.PRODUCTIVITY,
        description="Store dispute dossiers, parse PDF attachments, and organize evidence archives.",
        icon="file-text",
        status="coming_soon",
        supported_events=["file_uploaded", "file_shared"],
        available_actions=["upload_file", "search_files"]
    ),
    "notion": AppMetadata(
        app_id="notion",
        name="Notion",
        category=AppCategory.PRODUCTIVITY,
        description="Sync investigation dossiers and application statuses into internal team databases.",
        icon="database",
        status="coming_soon",
        supported_events=["page_created", "database_row_updated"],
        available_actions=["create_page", "query_database"]
    ),
    "linear": AppMetadata(
        app_id="linear",
        name="Linear",
        category=AppCategory.PROJECT,
        description="Create escalated engineering bugs and link customer billing discrepancies.",
        icon="check-circle",
        status="coming_soon",
        supported_events=["issue_created", "status_changed"],
        available_actions=["create_issue", "update_status"]
    ),
    "jira": AppMetadata(
        app_id="jira",
        name="Jira",
        category=AppCategory.PROJECT,
        description="Escalate financial anomalies to enterprise support and fraud prevention boards.",
        icon="layers",
        status="coming_soon",
        supported_events=["ticket_created", "status_updated"],
        available_actions=["create_ticket", "get_issue"]
    ),
    "discord": AppMetadata(
        app_id="discord",
        name="Discord",
        category=AppCategory.COMMUNICATION,
        description="Deliver agent notifications and student/community community alerts.",
        icon="send",
        status="coming_soon",
        supported_events=["message_received"],
        available_actions=["send_message", "read_channel"]
    )
}

# Predefined Tool Definitions
TOOLS_CATALOGUE: Dict[str, ToolDefinition] = {
    "gmail.search_messages": ToolDefinition(
        name="gmail.search_messages",
        app_id="gmail",
        display_name="Search Gmail Messages",
        description="Search Gmail inbox and sent items by query, sender, or subject.",
        action_type=ActionType.READ,
        requires_approval=False,
        parameters_schema={"query": "string", "limit": "integer"}
    ),
    "gmail.read_threads": ToolDefinition(
        name="gmail.read_threads",
        app_id="gmail",
        display_name="Read Gmail Threads",
        description="Fetch full message bodies and conversation threads from Gmail.",
        action_type=ActionType.READ,
        requires_approval=False,
        parameters_schema={"thread_id": "string"}
    ),
    "gmail.send_email": ToolDefinition(
        name="gmail.send_email",
        app_id="gmail",
        display_name="Send Gmail Email",
        description="Send an email to a customer, candidate, or external stakeholder.",
        action_type=ActionType.COMMUNICATION,
        requires_approval=True,
        parameters_schema={"to": "string", "subject": "string", "body": "string"}
    ),
    "stripe.search_charges": ToolDefinition(
        name="stripe.search_charges",
        app_id="stripe",
        display_name="Search Stripe Charges",
        description="Query Stripe ledger for customer charges, amounts, timestamps, and refund statuses.",
        action_type=ActionType.READ,
        requires_approval=False,
        parameters_schema={"customer_email": "string", "limit": "integer"}
    ),
    "stripe.get_customer": ToolDefinition(
        name="stripe.get_customer",
        app_id="stripe",
        display_name="Get Stripe Customer Details",
        description="Retrieve customer records, metadata, and subscriptions from Stripe.",
        action_type=ActionType.READ,
        requires_approval=False,
        parameters_schema={"email": "string"}
    ),
    "stripe.create_refund": ToolDefinition(
        name="stripe.create_refund",
        app_id="stripe",
        display_name="Create Stripe Refund",
        description="Execute a monetary refund against a Stripe charge ID (TEST mode only). High-risk financial action.",
        action_type=ActionType.FINANCIAL,
        requires_approval=True, # STRICT SAFETY INVARIANT
        parameters_schema={"charge_id": "string", "amount": "number", "reason": "string"}
    ),
    "slack.search_messages": ToolDefinition(
        name="slack.search_messages",
        app_id="slack",
        display_name="Search Slack Channels",
        description="Search team channels for customer context, discussions, and internal notes.",
        action_type=ActionType.READ,
        requires_approval=False,
        parameters_schema={"channel": "string", "query": "string"}
    ),
    "slack.post_message": ToolDefinition(
        name="slack.post_message",
        app_id="slack",
        display_name="Post Slack Notification",
        description="Post structured dossier, status updates, or high-priority alerts to a Slack channel.",
        action_type=ActionType.COMMUNICATION,
        requires_approval=False,
        parameters_schema={"channel": "string", "text": "string"}
    ),
    "slack.list_channels": ToolDefinition(
        name="slack.list_channels",
        app_id="slack",
        display_name="List Slack Channels",
        description="List public channels accessible to the agent bot.",
        action_type=ActionType.READ,
        requires_approval=False,
        parameters_schema={}
    )
}

class ToolRegistry:
    @staticmethod
    def get_all_apps() -> List[Dict[str, Any]]:
        """Returns catalogue of all apps with live connection status."""
        apps = []
        for app_id, app in APPS_CATALOGUE.items():
            data = app.dict()
            if app_id == "gmail":
                data["connected"] = os.path.exists(settings.GMAIL_TOKEN_PATH) or os.path.exists(settings.GMAIL_CREDENTIALS_PATH)
            elif app_id == "stripe":
                data["connected"] = bool(settings.STRIPE_SECRET_KEY)
            elif app_id == "slack":
                data["connected"] = bool(settings.SLACK_BOT_TOKEN)
            else:
                data["connected"] = False
            apps.append(data)
        return apps

    @staticmethod
    def get_app(app_id: str) -> Optional[AppMetadata]:
        return APPS_CATALOGUE.get(app_id)

    @staticmethod
    def get_available_tools(workspace_apps: List[str], permissions: Optional[Dict[str, Any]] = None) -> List[ToolDefinition]:
        """
        Filters tools strictly to those belonging to the workspace's connected apps.
        Guarantees workspace security isolation!
        """
        tools = []
        workspace_apps_set = set(workspace_apps or [])
        for tool_name, tool in TOOLS_CATALOGUE.items():
            if tool.app_id in workspace_apps_set:
                tool_copy = tool.copy()
                # Apply permission override if specified in workspace permissions
                if permissions and tool.app_id in permissions:
                    app_perms = permissions[tool.app_id]
                    if isinstance(app_perms, dict):
                        action_name = tool.name.split(".")[-1]
                        if action_name in app_perms:
                            perm_val = app_perms[action_name]
                            if perm_val == "APPROVAL_REQUIRED":
                                tool_copy.requires_approval = True
                            elif perm_val is False:
                                # Disabled for this workspace
                                continue
                    elif app_perms is False:
                        continue
                tools.append(tool_copy)
        return tools

    @staticmethod
    def verify_tool_access(workspace_apps: List[str], tool_name: str) -> ToolDefinition:
        """
        Strict security boundary check.
        Raises PermissionError if a workspace attempts to execute a tool from an unapproved app.
        """
        tool = TOOLS_CATALOGUE.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: '{tool_name}'")
        
        workspace_apps_set = set(workspace_apps or [])
        if tool.app_id not in workspace_apps_set:
            raise PermissionError(
                f"Security Violation: Tool '{tool_name}' belongs to app '{tool.app_id}', "
                f"which is NOT connected to this workspace. Allowed apps: {list(workspace_apps_set)}"
            )
        return tool

    @staticmethod
    def is_financial_or_high_risk(tool_name: str) -> bool:
        tool = TOOLS_CATALOGUE.get(tool_name)
        if not tool:
            return False
        return tool.action_type == ActionType.FINANCIAL or tool.requires_approval
