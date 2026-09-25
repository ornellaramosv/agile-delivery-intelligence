"""Load frozen sprint records outside the quality domain."""

import json
from pathlib import Path

from app.domain.quality_rework import calculate_quality_rework

SCENARIO_PATH = Path(__file__).resolve().parents[4] / "data" / "demo" / "sprint-08"


def sprint_08_quality_rework() -> dict:
    files = {"sprint": "sprint.json", "work_items": "work-items.json", "bugs": "bugs.json",
             "tasks": "tasks.json", "events": "delivery-events.json"}
    return calculate_quality_rework(**{
        key: json.loads((SCENARIO_PATH / filename).read_text(encoding="utf-8"))
        for key, filename in files.items()
    })
