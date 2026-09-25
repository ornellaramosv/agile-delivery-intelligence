"""Load the frozen demo fixture outside the Delivery Flow domain."""

import json
from pathlib import Path

from app.domain.delivery_flow import calculate_delivery_flow

SCENARIO_PATH = Path(__file__).resolve().parents[4] / "data" / "demo" / "sprint-08"


def sprint_08_delivery_flow() -> dict:
    def load(filename: str):
        return json.loads((SCENARIO_PATH / filename).read_text(encoding="utf-8"))

    return calculate_delivery_flow(
        sprint=load("sprint.json"),
        work_items=load("work-items.json"),
        events=load("delivery-events.json"),
    )
