import os
import sys
import json
import time
from datetime import datetime

# GitHub Actions free tier for private repos: 2,000 minutes/month
MONTHLY_LIMIT_MINUTES = 2000
SOFT_LIMIT_PERCENT = 0.75  # 1500 minutes -> Throttle
HARD_LIMIT_PERCENT = 0.90  # 1800 minutes -> Pause heavy sweeps

METRICS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage_metrics.json")

def load_metrics():
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_month": datetime.utcnow().strftime("%Y-%m"),
        "total_minutes_consumed": 0.0,
        "runs_count": 0,
        "history": []
    }

def save_metrics(metrics):
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def check_budget_status():
    metrics = load_metrics()
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    # Reset if new month
    if metrics.get("current_month") != current_month:
        metrics["current_month"] = current_month
        metrics["total_minutes_consumed"] = 0.0
        metrics["runs_count"] = 0
        save_metrics(metrics)

    consumed = metrics.get("total_minutes_consumed", 0.0)
    percent = consumed / MONTHLY_LIMIT_MINUTES

    if percent >= HARD_LIMIT_PERCENT:
        status = "PAUSED"
        action = "Skip heavy full sweeps to preserve quota. Only execute lightweight published recheck."
    elif percent >= SOFT_LIMIT_PERCENT:
        status = "THROTTLED"
        action = "Downscale candidate sweep batch size and increase test intervals."
    else:
        status = "HEALTHY"
        action = "Full candidate sweep and published recheck operating normally."

    return {
        "month": current_month,
        "consumed_minutes": round(consumed, 2),
        "limit_minutes": MONTHLY_LIMIT_MINUTES,
        "usage_percent": round(percent * 100, 1),
        "status": status,
        "recommended_action": action
    }

def record_run(workflow_name, duration_seconds, node_count, pass_count, fail_breakdown=None):
    metrics = load_metrics()
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    if metrics.get("current_month") != current_month:
        metrics["current_month"] = current_month
        metrics["total_minutes_consumed"] = 0.0
        metrics["runs_count"] = 0

    duration_minutes = duration_seconds / 60.0
    metrics["total_minutes_consumed"] = round(metrics["total_minutes_consumed"] + duration_minutes, 2)
    metrics["runs_count"] = metrics.get("runs_count", 0) + 1

    entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "workflow": workflow_name,
        "duration_sec": round(duration_seconds, 1),
        "duration_min": round(duration_minutes, 2),
        "nodes_tested": node_count,
        "nodes_passed": pass_count,
        "pass_rate": f"{round(pass_count / max(1, node_count) * 100, 1)}%",
        "fail_breakdown": fail_breakdown or {}
    }
    
    # Keep last 50 run records
    metrics.setdefault("history", []).append(entry)
    metrics["history"] = metrics["history"][-50:]
    
    save_metrics(metrics)
    return metrics

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        info = check_budget_status()
        print(json.dumps(info, indent=2, ensure_ascii=False))
        if info["status"] == "PAUSED":
            sys.exit(2)  # Signal to skip heavy job
        elif info["status"] == "THROTTLED":
            sys.exit(1)  # Signal to throttle
        else:
            sys.exit(0)
    else:
        info = check_budget_status()
        print(f"Monthly Budget Status [{info['month']}]: {info['consumed_minutes']}/{info['limit_minutes']} min ({info['usage_percent']}%) - {info['status']}")
