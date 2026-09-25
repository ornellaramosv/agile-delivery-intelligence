"""Replay delivery events into end-of-working-day snapshots, without I/O."""

from collections import defaultdict
from dataclasses import asdict
from datetime import date, datetime
from typing import Any

from .config import BurndownConfig

Record = dict[str, Any]


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError("Event and Bug timestamps must include a timezone")
    return parsed


def _index(records: list[Record]) -> dict[str, Record]:
    indexed = {record["id"]: record for record in records}
    if len(indexed) != len(records):
        raise ValueError("Record IDs must be unique")
    return indexed


def calculate_burndown(
    *,
    sprint: Record,
    work_items: list[Record],
    bugs: list[Record],
    events: list[Record],
    config: BurndownConfig | None = None,
) -> Record:
    """Return JSON-ready results. Input records are never mutated.

    Story final states and Task hours are deliberately not calculation inputs.
    Bug timestamps must agree with their corresponding delivery events.
    """
    settings = config if config is not None else BurndownConfig()
    items = _index(work_items)
    bug_by_id = _index(bugs)
    _index(events)
    baseline = set(sprint["original_baseline_work_item_ids"])
    if len(baseline) != len(sprint["original_baseline_work_item_ids"]):
        raise ValueError("Baseline IDs must be unique")
    if baseline != {item["id"] for item in work_items if item["original_baseline"]}:
        raise ValueError("Baseline membership must agree with Work Item flags")
    for item in work_items:
        if type(item["original_baseline"]) is not bool or type(item["scope_added_after_baseline"]) is not bool:
            raise ValueError("Story scope flags must be boolean")
        if item["original_baseline"] == item["scope_added_after_baseline"]:
            raise ValueError("Each story must belong to baseline or added scope, exclusively")
    for bug in bugs:
        if bug["work_item_id"] not in items:
            raise ValueError("Bug references an unknown story")
        if type(bug["blocks_story_closure"]) is not bool:
            raise ValueError("blocks_story_closure must be boolean")

    calendar = sprint["working_days"]
    if [entry["sprint_day"] for entry in calendar] != list(range(1, len(calendar) + 1)) or not calendar:
        raise ValueError("Working days must be consecutive, starting at 1")
    dates = [date.fromisoformat(entry["date"]) for entry in calendar]
    if dates != sorted(set(dates)):
        raise ValueError("Working-day dates must be unique and chronological")
    calendar_by_day = {entry["sprint_day"]: entry["date"] for entry in calendar}
    by_day: dict[int, list[Record]] = defaultdict(list)
    for event in sorted(events, key=lambda value: (_timestamp(value["timestamp"]), value["id"])):
        if event["work_item_id"] not in items:
            raise ValueError("Event references an unknown story")
        if calendar_by_day.get(event["sprint_day"]) != _timestamp(event["timestamp"]).date().isoformat():
            raise ValueError("Event timestamp must match its working day")
        by_day[event["sprint_day"]].append(event)

    states: dict[str, str] = {}
    added: set[str] = set()
    created: set[str] = set()
    resolved: set[str] = set()
    rework: set[str] = set()
    snapshots: list[Record] = []
    insights: list[Record] = []
    flat_days: list[Record] = []

    def finish_flatline() -> None:
        if len(flat_days) >= settings.flatline_threshold_days:
            insights.append({
                "type": "flatline",
                "start_day": flat_days[0]["sprint_day"],
                "end_day": flat_days[-1]["sprint_day"],
                "number_of_days": len(flat_days),
                "remaining_work": flat_days[-1]["current_remaining_work"],
                "contributing_context": [
                    {"sprint_day": snapshot["sprint_day"],
                     "causes": snapshot["explanation"]["causes"],
                     "event_ids": [event["id"] for event in by_day[snapshot["sprint_day"]]]}
                    for snapshot in flat_days
                ],
            })
        flat_days.clear()

    for entry in calendar:
        causes: list[Record] = []
        for event in by_day[entry["sprint_day"]]:
            item_id = event["work_item_id"]
            kind = event["event_type"]
            old, new = event["from_state"], event["to_state"]
            if old != states.get(item_id):
                raise ValueError("Story event history is not continuous")
            if kind == "scope_added":
                if item_id in baseline or item_id in added or old is not None:
                    raise ValueError("Scope addition must introduce a new non-baseline story")
                added.add(item_id)
                causes.append(_cause(event, "scope_added", item_id, 1))
            elif kind == "sprint_started":
                if item_id not in baseline or old is not None or entry["sprint_day"] != 1:
                    raise ValueError("Opening snapshots must establish baseline stories on Day 1")
            elif old is None:
                raise ValueError("Story must enter the sprint before other events")
            if item_id not in baseline | added:
                raise ValueError("Story has not formally entered the sprint")
            if old == "Closed" and new != "Closed":
                raise ValueError("Story reopening is outside the v0.1 event contract")

            bug_id = event.get("related_bug_id")
            if bug_id is not None:
                if bug_id not in bug_by_id or bug_by_id[bug_id]["work_item_id"] != item_id:
                    raise ValueError("Event Bug link must match its story")
            if kind in {"bug_detected", "bug_resolved", "returned_to_dev"}:
                if bug_id is None:
                    raise ValueError("Defect and rework events require a linked Bug")
                bug = bug_by_id[bug_id]
                if kind == "bug_detected":
                    if bug_id in created or _timestamp(bug["created_at"]) != _timestamp(event["timestamp"]):
                        raise ValueError("Bug creation event must match its unique creation timestamp")
                    created.add(bug_id)
                    if bug["blocks_story_closure"]:
                        causes.append(_cause(event, "closure_blocking_bug_created", bug_id, 1))
                elif kind == "bug_resolved":
                    if bug_id not in created or bug_id in resolved or not bug["resolved_at"]:
                        raise ValueError("Bug resolution requires an existing unresolved Bug")
                    if _timestamp(bug["resolved_at"]) != _timestamp(event["timestamp"]):
                        raise ValueError("Bug resolution timestamp must match its event")
                    resolved.add(bug_id)
                    if bug["blocks_story_closure"]:
                        causes.append(_cause(event, "closure_blocking_bug_resolved", bug_id, -1))
                else:
                    if (old, new) != ("QA", "Returned to DEV") or bug_id not in created - resolved:
                        raise ValueError("QA rejection requires an existing unresolved Bug")
                    rework.add(bug_id)
            if new == "Closed" and old != "Closed":
                if any(bug_by_id[key]["work_item_id"] == item_id and bug_by_id[key]["blocks_story_closure"] for key in created - resolved):
                    raise ValueError("Story cannot close with an unresolved story-closure Bug")
                causes.append(_cause(event, "story_closed", item_id, -1))
            states[item_id] = new

        if not baseline <= states.keys():
            raise ValueError("Every baseline story requires an opening snapshot")
        open_baseline = sorted(key for key in baseline if states[key] != "Closed")
        open_added = sorted(key for key in added if states[key] != "Closed")
        open_bugs = sorted(key for key in created - resolved if bug_by_id[key]["blocks_story_closure"])
        remaining = len(open_baseline) + len(open_added) + len(open_bugs)
        previous = snapshots[-1]["current_remaining_work"] if snapshots else None
        delta = remaining - previous if previous is not None else None
        movement = None if delta is None else "up" if delta > 0 else "down" if delta < 0 else "flat"
        if delta is not None and delta != sum(cause["effect"] for cause in causes):
            raise ValueError("Daily causes must reconcile with the remaining-work change")
        snapshot = {
            **entry,
            "original_baseline": len(baseline),
            "open_baseline_stories": len(open_baseline),
            "open_scope_added_stories": len(open_added),
            "open_closure_blocking_bugs": len(open_bugs),
            "current_remaining_work": remaining,
            "closed_baseline_stories": len(baseline) - len(open_baseline),
            "closed_scope_added_stories": len(added) - len(open_added),
            "scope_added_total": len(added),
            "active_rework_bugs": sorted(rework & (created - resolved)),
            "composition": {
                "open_baseline_story_ids": open_baseline,
                "open_scope_added_story_ids": open_added,
                "open_closure_blocking_bug_ids": open_bugs,
            },
            "explanation": {"day": entry["sprint_day"], "movement": movement, "delta": delta, "causes": causes},
        }
        snapshots.append(snapshot)
        if movement == "up":
            insights.append({"type": "upward_movement", "sprint_day": entry["sprint_day"],
                             "previous_remaining": previous, "current_remaining": remaining,
                             "delta": delta, "causes": causes})
        if movement == "flat":
            flat_days.append(snapshot)
        else:
            finish_flatline()
    finish_flatline()
    if created != set(bug_by_id) or resolved != {bug["id"] for bug in bugs if bug["resolved_at"] is not None}:
        raise ValueError("Bug lifecycle records require matching delivery events within the sprint")
    return {
        "sprint": {key: sprint[key] for key in ("id", "name", "project", "backlog", "start_date", "end_date", "timezone")},
        "configuration": asdict(settings),
        "daily_snapshots": snapshots,
        "insights": sorted(insights, key=lambda insight: (insight.get("sprint_day", insight.get("end_day")), insight["type"])),
    }


def _cause(event: Record, kind: str, record_id: str, effect: int) -> Record:
    return {"type": kind, "id": record_id, "work_item_id": event["work_item_id"],
            "effect": effect, "event_id": event["id"], "timestamp": event["timestamp"]}
