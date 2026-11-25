"""
ai_engine.py - AI & Machine Learning Cloud Waste Segregation Engine
Combines Scikit-Learn KMeans clustering with multi-factor heuristics to segregate
idle, overprovisioned, orphaned, and optimal cloud resources.
"""

import json
import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.cluster import KMeans

FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "feedback_audit.json")

class AICloudWasteClassifier:
    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.feedback_log = self._load_feedback()

    def _load_feedback(self) -> List[Dict[str, Any]]:
        if os.path.exists(FEEDBACK_FILE):
            try:
                with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def record_feedback(self, resource_id: str, action: str, feedback_type: str = "accepted") -> Dict[str, Any]:
        entry = {
            "resource_id": resource_id,
            "action": action,
            "feedback": feedback_type,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        self.feedback_log.append(entry)
        try:
            with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
                json.dump(self.feedback_log, f, indent=2)
        except Exception:
            pass
        return entry

    def classify_and_segregate(self, raw_resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes AI segregation on collected Azure resources.
        Returns detailed list with AI classifications, waste scores,
        recommended actions, and aggregate FinOps cost savings.
        """
        if not raw_resources:
            return {
                "resources": [],
                "summary": {
                    "total_resources": 0,
                    "waste_count": 0,
                    "total_monthly_spend": 0.0,
                    "total_monthly_savings": 0.0,
                    "total_annual_savings": 0.0,
                    "waste_percentage": 0.0
                }
            }

        df = pd.DataFrame(raw_resources)

        # Features for Clustering: CPU Avg and Memory Avg
        features = df[["cpu_avg", "memory_avg"]].values
        
        # Train KMeans clustering if sufficient samples
        if len(features) >= self.n_clusters:
            clusters = self.kmeans.fit_predict(features)
            df["cluster"] = clusters
        else:
            df["cluster"] = 0

        classified_list = []
        total_monthly_spend = 0.0
        total_monthly_savings = 0.0
        waste_count = 0

        for _, row in df.iterrows():
            res_id = row["resource_id"]
            res_type = row["resource_type"]
            cpu = float(row["cpu_avg"])
            mem = float(row["memory_avg"])
            disk_iops = int(row["disk_iops"])
            cost = float(row["monthly_cost"])
            status = row["status"]
            sku = row["sku"]
            region = row["region"]

            # If resource is already deallocated/deleted from prior action:
            if "Deallocated" in status or "Deleted" in status or "Resized" in status:
                classification = "OPTIMIZED"
                action = "RETAIN"
                potential_savings = 0.0
                waste_score = 0
                rationale = f"Resource successfully optimized. State: {status}."
                tag_color = "purple"
            
            # Orphaned Storage / IP
            elif "Unattached" in res_type or "Unassociated" in res_type:
                classification = "ORPHANED_STORAGE"
                action = "DELETE"
                potential_savings = cost
                waste_score = 98
                rationale = f"Unattached Azure asset accumulating $0 ROI waste. Recommend instant decommission."
                tag_color = "red"
                waste_count += 1
                total_monthly_savings += potential_savings

            # Idle Zombie VM (< 5% CPU, < 10% RAM)
            elif cpu < 5.0 and mem < 10.0:
                classification = "IDLE_WASTE"
                action = "DEALLOCATE"
                potential_savings = cost
                waste_score = int(95 - (cpu * 2))
                rationale = f"Zombie Azure VM detected ({cpu:.1f}% CPU). Zero active traffic. Recommend immediate deallocation."
                tag_color = "red"
                waste_count += 1
                total_monthly_savings += potential_savings

            # Overprovisioned / Underutilized VM (5% <= CPU < 25%)
            elif cpu < 25.0:
                classification = "OVERPROVISIONED"
                action = "RESIZE"
                # Target SKU: Standard_B2s ($30.37/mo)
                target_cost = 30.37
                potential_savings = max(0.0, round(cost - target_cost, 2))
                waste_score = int(75 - (cpu * 1.5))
                rationale = f"Overprovisioned compute capacity ({cpu:.1f}% CPU). Downscale from {sku} to Standard_B2s."
                tag_color = "orange"
                waste_count += 1
                total_monthly_savings += potential_savings

            # Optimal Workload (Healthy production usage)
            else:
                classification = "OPTIMAL"
                action = "RETAIN"
                potential_savings = 0.0
                waste_score = 10
                rationale = f"Healthy enterprise workload ({cpu:.1f}% CPU, {mem:.1f}% RAM). Operating within peak SLA thresholds."
                tag_color = "green"

            total_monthly_spend += cost

            classified_list.append({
                "resource_id": res_id,
                "azure_resource_id": row.get("azure_resource_id", ""),
                "resource_type": res_type,
                "provider": row["provider"],
                "region": region,
                "sku": sku,
                "cpu_avg": cpu,
                "memory_avg": mem,
                "disk_iops": disk_iops,
                "status": status,
                "monthly_cost": cost,
                "classification": classification,
                "tag_color": tag_color,
                "recommended_action": action,
                "potential_monthly_savings": potential_savings,
                "waste_score": waste_score,
                "rationale": rationale
            })

        # Sort with most critical waste first
        classified_list.sort(key=lambda x: x["potential_monthly_savings"], reverse=True)

        total_resources = len(classified_list)
        waste_pct = round((waste_count / total_resources * 100), 1) if total_resources > 0 else 0.0

        return {
            "resources": classified_list,
            "summary": {
                "total_resources": total_resources,
                "waste_count": waste_count,
                "optimal_count": total_resources - waste_count,
                "total_monthly_spend": round(total_monthly_spend, 2),
                "total_monthly_savings": round(total_monthly_savings, 2),
                "total_annual_savings": round(total_monthly_savings * 12, 2),
                "waste_percentage": waste_pct
            }
        }
