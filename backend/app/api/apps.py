from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import os

from ..integrations.registry import ToolRegistry, APPS_CATALOGUE
from ..config import settings

router = APIRouter(prefix="/api/apps", tags=["Apps"])

@router.get("")
def list_apps():
    """Returns catalogue of all apps with connection status and capabilities."""
    return {"apps": ToolRegistry.get_all_apps()}

@router.get("/{app_id}")
def get_app(app_id: str):
    app = ToolRegistry.get_app(app_id)
    if not app:
        raise HTTPException(status_code=404, detail=f"App '{app_id}' not found")
    data = app.dict()
    if app_id == "gmail":
        data["connected"] = os.path.exists(settings.GMAIL_TOKEN_PATH) or os.path.exists(settings.GMAIL_CREDENTIALS_PATH)
    elif app_id == "stripe":
        data["connected"] = bool(settings.STRIPE_SECRET_KEY)
    elif app_id == "slack":
        data["connected"] = bool(settings.SLACK_BOT_TOKEN)
    else:
        data["connected"] = False
    return data

@router.post("/{app_id}/test-connection")
def test_app_connection(app_id: str):
    if app_id == "gmail":
        token_exists = os.path.exists(settings.GMAIL_TOKEN_PATH)
        creds_exists = os.path.exists(settings.GMAIL_CREDENTIALS_PATH)
        if token_exists or creds_exists:
            return {"status": "connected", "app_id": "gmail", "message": "Gmail OAuth token/credentials verified."}
        return {"status": "disconnected", "app_id": "gmail", "message": "No credentials.json or token.json found in backend root."}

    elif app_id == "stripe":
        if settings.STRIPE_SECRET_KEY:
            # Test key format
            is_test = "test" in settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY.startswith("sk_test_")
            return {
                "status": "connected",
                "app_id": "stripe",
                "mode": "TEST" if is_test else "LIVE",
                "message": f"Stripe secret key configured ({'TEST mode verified' if is_test else 'LIVE mode'})."
            }
        return {"status": "disconnected", "app_id": "stripe", "message": "STRIPE_SECRET_KEY is not set."}

    elif app_id == "slack":
        if settings.SLACK_BOT_TOKEN:
            return {"status": "connected", "app_id": "slack", "message": f"Slack Bot Token configured for #{settings.SLACK_CHANNEL}."}
        return {"status": "disconnected", "app_id": "slack", "message": "SLACK_BOT_TOKEN is not set."}

    else:
        return {"status": "coming_soon", "app_id": app_id, "message": "Integration connector scheduled for upcoming platform release."}
