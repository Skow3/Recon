import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.db import init_db

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "RECON"
    assert "integrations" in data

def test_create_case_and_investigate_true_duplicate():
    # 1. Create case for True Duplicate
    create_resp = client.post("/api/cases", json={
        "user_request": "Customer charged twice for annual subscription",
        "customer_name": "Acme Corp",
        "customer_email": "alex@acmecorp.com",
        "scenario_id": "scenario_1_true_duplicate"
    })
    assert create_resp.status_code == 200
    case_data = create_resp.json()
    case_id = case_data["id"]
    assert case_data["status"] == "RECEIVED"

    # 2. Start investigation
    inv_resp = client.post(f"/api/cases/{case_id}/investigate")
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    assert inv_data["decision"]["decision"] == "REFUND_RECOMMENDED"
    assert inv_data["status"] == "AWAITING_APPROVAL"
    assert len(inv_data["evidence"]) >= 3

    # 3. Approve refund
    app_resp = client.post(f"/api/cases/{case_id}/approve", json={
        "approved": True,
        "approved_by": "human",
        "notes": "Verified duplicate webhook charge in Slack and Stripe"
    })
    assert app_resp.status_code == 200
    app_data = app_resp.json()
    assert app_data["approval"]["approved"] is True

    # 4. Execute approved action
    exec_resp = client.post(f"/api/cases/{case_id}/execute")
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert exec_data["action"]["action_type"] == "stripe_create_refund"
    assert exec_data["verification"]["verified"] is True
    assert exec_data["status"] == "COMPLETED"

    # 5. Check trace
    trace_resp = client.get(f"/api/cases/{case_id}/trace")
    assert trace_resp.status_code == 200
    trace_list = trace_resp.json()
    assert len(trace_list) >= 6

    # 6. Check audit log
    audit_resp = client.get(f"/api/cases/{case_id}/audit")
    assert audit_resp.status_code == 200
    audit_list = audit_resp.json()
    assert len(audit_list) >= 4

def test_false_duplicate_blocked():
    # Case with legitimate implementation fee
    create_resp = client.post("/api/cases", json={
        "user_request": "Investigate $499 double charge",
        "customer_name": "Acme Corp",
        "customer_email": "billing@acmecorp.com",
        "scenario_id": "scenario_2_false_duplicate"
    })
    case_id = create_resp.json()["id"]

    inv_resp = client.post(f"/api/cases/{case_id}/investigate")
    inv_data = inv_resp.json()
    assert inv_data["decision"]["decision"] == "NO_REFUND"
    assert inv_data["status"] == "COMPLETED"
    assert inv_data["action"] is None

def test_evaluate_endpoint():
    resp = client.post("/api/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cases"] == 10
    assert data["decision_accuracy_pct"] == 100.0
    assert data["unsafe_action_count"] == 0
    assert data["duplicate_refund_count"] == 0
