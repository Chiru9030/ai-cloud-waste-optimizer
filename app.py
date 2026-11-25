"""
app.py - AI-Powered Cloud Waste Segregation System (Azure Edition)
Flask API & Interactive Web Dashboard Server with full CORS support.
"""

import os
import json
from flask import Flask, jsonify, request, render_template
from azure_manager import AzureCloudManager
from ai_engine import AICloudWasteClassifier

app = Flask(__name__)

# Initialize Managers
azure_mgr = AzureCloudManager()
ai_classifier = AICloudWasteClassifier()

# Enable Global CORS without third-party library dependencies
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response

@app.route("/", methods=["GET"])
def index():
    """Serves the executive-grade Web Dashboard."""
    return render_template("dashboard.html")

@app.route("/recommendations", methods=["GET", "OPTIONS"])
@app.route("/api/resources", methods=["GET", "OPTIONS"])
def get_recommendations():
    """
    Core API endpoint consumed by the Chrome Extension (popup.js) and Web Dashboard.
    Scans Azure infrastructure, passes telemetry to AI classifier, and returns recommendations.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    raw_resources = azure_mgr.fetch_resources()
    segregated = ai_classifier.classify_and_segregate(raw_resources)
    azure_info = azure_mgr.get_connection_status()

    # Note: 'results' key matches Chrome Extension popup.js expectation
    return jsonify({
        "status": "success",
        "azure": azure_info,
        "summary": segregated["summary"],
        "results": segregated["resources"]
    }), 200

@app.route("/api/action", methods=["POST", "OPTIONS"])
def execute_action():
    """Executes an Azure FinOps remediation action (DEALLOCATE, RESIZE, DELETE)."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    payload = request.get_json() or {}
    resource_id = payload.get("resource_id")
    action = payload.get("action", "DEALLOCATE")

    if not resource_id:
        return jsonify({"success": False, "error": "Missing resource_id parameter"}), 400

    # 1. Execute on Azure Cloud Manager
    result = azure_mgr.execute_azure_action(resource_id, action)

    # 2. Record feedback for AI Continuous Learning
    ai_classifier.record_feedback(resource_id, action, feedback_type="accepted")

    return jsonify(result), 200

@app.route("/api/optimize-all", methods=["POST", "OPTIONS"])
def optimize_all():
    """Bulk-executes optimization on all non-optimal resources."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    raw_resources = azure_mgr.fetch_resources()
    segregated = ai_classifier.classify_and_segregate(raw_resources)
    
    executed = []
    for res in segregated["resources"]:
        action = res.get("recommended_action")
        if action and action != "RETAIN":
            res_id = res["resource_id"]
            res_out = azure_mgr.execute_azure_action(res_id, action)
            ai_classifier.record_feedback(res_id, action, feedback_type="bulk_approved")
            executed.append(res_out)

    return jsonify({
        "success": True,
        "message": f"Successfully executed {len(executed)} Azure optimization actions.",
        "executed_count": len(executed),
        "actions": executed
    }), 200

@app.route("/api/reset", methods=["POST", "OPTIONS"])
def reset_simulation():
    """Resets all simulation states back to baseline."""
    azure_mgr.reset_simulation()
    return jsonify({"success": True, "message": "Azure environment baseline reset."}), 200

@app.route("/api/azure/status", methods=["GET", "OPTIONS"])
def get_azure_status():
    """Returns Azure connection details."""
    return jsonify(azure_mgr.get_connection_status()), 200

@app.route("/api/trends", methods=["GET"])
def get_trends():
    """Provides 6-month historical cloud waste & savings trends for visual analytics."""
    trends = [
        {"month": "Jun", "cloud_spend": 2450.0, "waste_cost": 890.0, "savings": 0.0},
        {"month": "Jul", "cloud_spend": 2620.0, "waste_cost": 940.0, "savings": 120.0},
        {"month": "Aug", "cloud_spend": 2510.0, "waste_cost": 850.0, "savings": 310.0},
        {"month": "Sep", "cloud_spend": 2300.0, "waste_cost": 670.0, "savings": 540.0},
        {"month": "Oct", "cloud_spend": 2180.0, "waste_cost": 590.0, "savings": 680.0},
        {"month": "Nov", "cloud_spend": 1820.0, "waste_cost": 410.0, "savings": 890.0}
    ]
    return jsonify({"trends": trends}), 200

@app.route("/api/feedback", methods=["POST", "OPTIONS"])
def submit_feedback():
    """Continuous learning feedback loop from administrators."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json() or {}
    resource_id = data.get("resource_id")
    action = data.get("action")
    feedback = data.get("feedback", "accepted")

    entry = ai_classifier.record_feedback(resource_id, action, feedback)
    return jsonify({"success": True, "recorded": entry}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"🚀 AI-Powered Cloud Waste Segregation System (Azure Edition) running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
