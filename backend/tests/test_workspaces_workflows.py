import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.db import init_db, SessionLocal
from app.api.workspaces import ensure_default_workspaces
from app.integrations.registry import ToolRegistry

@pytest.fixture(autouse=True)
def setup_data():
    init_db()

client = TestClient(app)

def test_list_workspaces_contains_defaults():
    resp = client.get("/api/workspaces")
    assert resp.status_code == 200
    data = resp.json()
    assert "workspaces" in data
    ws_ids = [w["id"] for w in data["workspaces"]]
    assert "ws_finance" in ws_ids
    assert "ws_internships" in ws_ids

    # Verify finance workspace properties
    finance = next(w for w in data["workspaces"] if w["id"] == "ws_finance")
    assert "stripe" in finance["connected_apps"]
    assert "gmail" in finance["connected_apps"]
    assert "slack" in finance["connected_apps"]
    # Verify tools include stripe.create_refund
    tool_names = [t["name"] for t in finance["available_tools"]]
    assert "stripe.create_refund" in tool_names

    # Verify internship workspace properties
    intern = next(w for w in data["workspaces"] if w["id"] == "ws_internships")
    assert "stripe" not in intern["connected_apps"]
    assert "gmail" in intern["connected_apps"]
    assert "slack" in intern["connected_apps"]
    intern_tool_names = [t["name"] for t in intern["available_tools"]]
    assert "stripe.create_refund" not in intern_tool_names
    assert "gmail.search_messages" in intern_tool_names

def test_security_boundary_enforcement():
    # Internship workspace connected apps do NOT include stripe
    with pytest.raises(PermissionError) as exc_info:
        ToolRegistry.verify_tool_access(["gmail", "slack"], "stripe.create_refund")
    assert "Security Violation" in str(exc_info.value)
    assert "stripe" in str(exc_info.value)

def test_interpret_goal():
    resp = client.post("/api/workflows/interpret-goal", json={
        "goal": "Monitor Gmail for internship responses, reject spam, extract interview deadlines, and notify Slack",
        "workspace_id": "ws_internships"
    })
    assert resp.status_code == 200
    plan = resp.json()
    assert "workflow_name" in plan
    assert "plan_steps" in plan
    assert len(plan["plan_steps"]) == 7
    assert plan["approval_required"] is False
    assert "gmail" in plan["recommended_apps"]

def test_internship_monitor_workflow_run():
    # 1. Run interview invite scenario
    resp = client.post("/api/workflows/wf_internship_monitor/run", json={
        "scenario_key": "stripe_interview",
        "force_reprocess": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["extracted_data"]["company"] == "Stripe"
    assert data["extracted_data"]["importance"] == "HIGH"
    assert data["extracted_data"]["action_required"] is True
    assert data["verification_result"]["verified"] is True

    # 2. Test duplicate event prevention (idempotency)
    dedup_resp = client.post("/api/workflows/wf_internship_monitor/run", json={
        "scenario_key": "stripe_interview",
        "force_reprocess": False
    })
    assert dedup_resp.status_code == 200
    dedup_data = dedup_resp.json()
    assert dedup_data["status"] == "SKIPPED_DUPLICATE"

    # 3. Test noise suppression (newsletter)
    spam_resp = client.post("/api/workflows/wf_internship_monitor/run", json={
        "scenario_key": "newsletter_spam",
        "force_reprocess": True
    })
    assert spam_resp.status_code == 200
    spam_data = spam_resp.json()
    assert spam_data["extracted_data"]["importance"] == "LOW"
    assert spam_data["action_result"]["status"] == "SUPPRESSED"

def test_apps_catalogue():
    resp = client.get("/api/apps")
    assert resp.status_code == 200
    apps = resp.json()["apps"]
    app_ids = [a["app_id"] for a in apps]
    for required in ["gmail", "stripe", "slack", "github", "google_calendar", "notion"]:
        assert required in app_ids

    # Test connection test endpoint
    test_resp = client.post("/api/apps/stripe/test-connection")
    assert test_resp.status_code == 200
    assert "status" in test_resp.json()
