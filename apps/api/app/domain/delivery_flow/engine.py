"""Pure end-of-day workflow replay; no Bug, Task, or presentation logic."""

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

WORKFLOW_STATES = (
    "Development", "Code Integration", "Ready for QA", "QA",
    "Returned to DEV", "Blocked", "Closed",
)
Record = dict[str, Any]


def calculate_delivery_flow(
    *, sprint: Record, work_items: list[Record], events: list[Record],
) -> Record:
    """Replay scope entries and transitions; final item snapshots are not inputs."""
    items = {item["id"]: item for item in work_items}
    if len(items) != len(work_items):
        raise ValueError("Work Item IDs must be unique")
    baseline = set(sprint["original_baseline_work_item_ids"])
    if len(baseline) != len(sprint["original_baseline_work_item_ids"]):
        raise ValueError("Baseline IDs must be unique")
    if baseline != {item["id"] for item in work_items if item["original_baseline"]}:
        raise ValueError("Baseline membership must match Work Items")
    for item in work_items:
        if (item["type"] != "User Story"
                or type(item["original_baseline"]) is not bool
                or type(item["scope_added_after_baseline"]) is not bool
                or item["original_baseline"] == item["scope_added_after_baseline"]):
            raise ValueError("Each User Story must be baseline or scope added")

    days = sprint["working_days"]
    if not days or [d["sprint_day"] for d in days] != list(range(1, len(days) + 1)):
        raise ValueError("Working days must be consecutive sprint-day numbers")
    dates = [date.fromisoformat(d["date"]) for d in days]
    if dates != sorted(set(dates)):
        raise ValueError("Working dates must be unique and chronological")
    timezone = ZoneInfo(sprint["timezone"])
    by_day: dict[int, list[tuple[datetime, Record]]] = {d["sprint_day"]: [] for d in days}
    event_ids: set[str] = set()
    for event in events:
        if event["id"] in event_ids:
            raise ValueError("Event IDs must be unique")
        event_ids.add(event["id"])
        if event["work_item_id"] not in items:
            raise ValueError("Event references an unknown Work Item")
        day = event["sprint_day"]
        timestamp = datetime.fromisoformat(event["timestamp"])
        if (type(day) is not int or day not in by_day or timestamp.tzinfo is None
                or timestamp.astimezone(timezone).date() != dates[day - 1]):
            raise ValueError("Event timestamp must match its working day and include a timezone")
        for key in ("from_state", "to_state"):
            if event[key] is not None and event[key] not in WORKFLOW_STATES:
                raise ValueError("Event uses an unknown workflow state")
        by_day[day].append((timestamp, event))

    current: dict[str, str] = {}
    snapshots = []
    daily_movements = []
    for day in days:
        movements = []
        entries = []
        for _, event in sorted(by_day[day["sprint_day"]], key=lambda pair: (pair[0], pair[1]["id"])):
            item_id = event["work_item_id"]
            before, after = event["from_state"], event["to_state"]
            evidence = {
                "event_id": event["id"], "work_item_id": item_id,
                "timestamp": event["timestamp"], "from_state": before, "to_state": after,
            }
            if event["event_type"] in ("sprint_started", "scope_added"):
                is_baseline = item_id in baseline
                expected_type = "sprint_started" if is_baseline else "scope_added"
                if (item_id in current or before is not None or after is None
                        or event["event_type"] != expected_type
                        or (is_baseline and day["sprint_day"] != 1)):
                    raise ValueError("Invalid or duplicate scope entry")
                current[item_id] = after
                entries.append(evidence)
            else:
                if item_id not in current:
                    raise ValueError("Event precedes formal scope entry")
                # Null/null and same-state records provide context, never a transition.
                if before is None and after is None:
                    continue
                if before != current[item_id] or after is None:
                    raise ValueError("Discontinuous workflow history")
                if before != after:
                    current[item_id] = after
                    movements.append(evidence)
        if day["sprint_day"] == 1 and not baseline.issubset(current):
            raise ValueError("Every baseline story needs a Day 1 opening event")
        story_states = dict(sorted(current.items()))
        counts = {state: sum(value == state for value in story_states.values())
                  for state in WORKFLOW_STATES}
        closed = counts["Closed"]
        snapshots.append({
            **day, "states": counts, "story_states": story_states,
            "open_stories": len(current) - closed, "closed_stories": closed,
            "total_active_scope": len(current),
        })
        daily_movements.append({**day, "movements": movements, "scope_entries": entries})

    return {
        "sprint": {key: sprint[key] for key in (
            "id", "name", "project", "backlog", "start_date", "end_date", "timezone",
        )},
        "workflow_states": list(WORKFLOW_STATES),
        "daily_snapshots": snapshots,
        "daily_movements": daily_movements,
    }
