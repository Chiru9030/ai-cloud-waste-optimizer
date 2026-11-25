"""
test_system.py - End-to-End Verification Suite for AI Cloud Waste Segregation (Azure)
"""

import sys
import json
from app import app
from azure_manager import AzureCloudManager
from ai_engine import AICloudWasteClassifier

def test_azure_manager():
    print("[1/4] Testing Azure Cloud Manager...")
    mgr = AzureCloudManager()
    status = mgr.get_connection_status()
    print(f"      Connection Mode: {status['mode']}")
    assert status["provider"] == "Microsoft Azure"

    resources = mgr.fetch_resources()
    print(f"      Fetched {len(resources)} Azure resources.")
    assert len(resources) > 0
    assert any("az-vm" in r["resource_id"] for r in resources)
    print("      ✓ Azure Manager Test Passed.")
    return mgr, resources

def test_ai_engine(resources):
    print("[2/4] Testing AI & Machine Learning Classification Engine...")
    classifier = AICloudWasteClassifier()
    result = classifier.classify_and_segregate(resources)
    
    summary = result["summary"]
    print(f"      Total Resources: {summary['total_resources']}")
    print(f"      Identified Waste: {summary['waste_count']} ({summary['waste_percentage']}%)")
    print(f"      Monthly Savings Identified: ${summary['total_monthly_savings']}")
    print(f"      Annual Savings Forecast: ${summary['total_annual_savings']}")

    assert summary["waste_count"] > 0
    assert summary["total_monthly_savings"] > 0
    
    # Check that classifications match expected categories
    classes = {r["classification"] for r in result["resources"]}
    print(f"      Discovered Waste Classes: {classes}")
    assert "IDLE_WASTE" in classes
    assert "OVERPROVISIONED" in classes
    print("      ✓ AI Classification Test Passed.")
    return classifier

def test_flask_endpoints():
    print("[3/4] Testing Flask API Endpoints & CORS Headers...")
    client = app.test_client()

    # 1. Test / (Dashboard HTML)
    res = client.get("/")
    assert res.status_code == 200
    assert b"AI Cloud Waste Segregation" in res.data
    print("      ✓ GET / (Dashboard HTML) returned 200 OK.")

    # 2. Test /recommendations (used by Chrome Extension)
    res = client.get("/recommendations")
    assert res.status_code == 200
    assert res.headers.get("Access-Control-Allow-Origin") == "*"
    data = json.loads(res.data)
    assert "results" in data
    assert "summary" in data
    assert "azure" in data
    print(f"      ✓ GET /recommendations returned {len(data['results'])} assets with CORS.")

    # 3. Test /api/action (Single remediation)
    test_target = data["results"][0]["resource_id"]
    test_action = data["results"][0]["recommended_action"]
    res = client.post("/api/action", json={"resource_id": test_target, "action": test_action})
    assert res.status_code == 200
    action_data = json.loads(res.data)
    assert action_data["success"] is True
    print(f"      ✓ POST /api/action executed {test_action} on {test_target}.")

    # 4. Test /api/optimize-all (Bulk remediation)
    res = client.post("/api/optimize-all")
    assert res.status_code == 200
    bulk_data = json.loads(res.data)
    assert bulk_data["success"] is True
    print(f"      ✓ POST /api/optimize-all executed {bulk_data['executed_count']} remediations.")

    # 5. Test /api/trends
    res = client.get("/api/trends")
    assert res.status_code == 200
    trends_data = json.loads(res.data)
    assert len(trends_data["trends"]) == 6
    print("      ✓ GET /api/trends returned historical 6-month telemetry.")

    # 6. Test /api/reset
    res = client.post("/api/reset")
    assert res.status_code == 200
    print("      ✓ POST /api/reset environment successfully reset.")

def run_all_tests():
    print("============================================================")
    print("  AI CLOUD WASTE SEGREGATION SYSTEM - VERIFICATION SUITE   ")
    print("============================================================")
    mgr, resources = test_azure_manager()
    test_ai_engine(resources)
    test_flask_endpoints()
    print("[4/4] All System Checks Passed Successfully! Ready for Demo.")
    print("============================================================")

if __name__ == "__main__":
    run_all_tests()
