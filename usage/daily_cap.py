import json
import os
from datetime import date
from pathlib import Path

USAGE_FILE = "usage/daily_usage.json"
DAILY_LIMIT = 100  # Global requests per day across ALL users


def get_usage() -> dict:
    """Load current usage from file. Returns fresh dict if file missing or stale."""
    Path("usage").mkdir(exist_ok=True)
    today = str(date.today())

    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f:
                data = json.load(f)
            if data.get("date") != today:
                return {"date": today, "count": 0}
            return data
        except Exception:
            pass
    return {"date": today, "count": 0}


def increment_usage() -> int:
    """Increment counter and return new count."""
    data = get_usage()
    data["count"] += 1
    Path("usage").mkdir(exist_ok=True)
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f)
    return data["count"]


def is_limit_reached() -> bool:
    """Returns True if daily limit has been hit."""
    return get_usage()["count"] >= DAILY_LIMIT


def get_remaining() -> int:
    """Returns requests remaining today."""
    return max(0, DAILY_LIMIT - get_usage()["count"])


def get_usage_percentage() -> float:
    """Returns usage as a percentage of daily limit."""
    return (get_usage()["count"] / DAILY_LIMIT) * 100
