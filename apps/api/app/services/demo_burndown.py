"""Load the repository fixture; keep filesystem access outside the domain."""

import json
from pathlib import Path

from app.domain.burndown import BurndownConfig, calculate_burndown

SCENARIO_PATH = Path(__file__).resolve().parents[4] / "data" / "demo" / "sprint-08"


def sprint_08_burndown(config: BurndownConfig | None = None) -> dict:
    def load(filename: str):
        return json.loads((SCENARIO_PATH / filename).read_text(encoding="utf-8"))

    return calculate_burndown(
        sprint=load("sprint.json"),
        work_items=load("work-items.json"),
        bugs=load("bugs.json"),
        events=load("delivery-events.json"),
        config=config,
    )
