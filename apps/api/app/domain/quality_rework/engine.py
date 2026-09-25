"""Deterministic quality analysis of the sprint event and effort records."""

from datetime import datetime
from math import isfinite
from typing import Any

from app.domain.delivery_flow import calculate_delivery_flow

Record = dict[str, Any]


def _index(records: list[Record], label: str) -> dict[str, Record]:
    result = {record["id"]: record for record in records}
    if len(result) != len(records):
        raise ValueError(f"Duplicate {label} IDs")
    return result


def _effort(tasks: list[Record]) -> Record:
    return {
        "tasks": len(tasks), "task_ids": sorted(task["id"] for task in tasks),
        **{field: sum(task[field] for task in tasks) for field in (
            "estimated_hours", "completed_hours", "remaining_hours",
        )},
    }


def calculate_quality_rework(
    *, sprint: Record, work_items: list[Record], bugs: list[Record],
    tasks: list[Record], events: list[Record],
) -> Record:
    """Use validated event replay for scope/state; QA acceptance is explicit evidence."""
    flow = calculate_delivery_flow(sprint=sprint, work_items=work_items, events=events)
    items = _index(work_items, "Work Item")
    bug_index = _index(bugs, "Bug")
    _index(tasks, "Task")
    for record in bugs + tasks:
        if record["work_item_id"] not in items:
            raise ValueError("Bug or Task references an unknown Work Item")
    for record in events + tasks:
        bug_id = record.get("related_bug_id")
        if bug_id and (bug_id not in bug_index
                       or bug_index[bug_id]["work_item_id"] != record["work_item_id"]):
            raise ValueError("Bug evidence must reference the same User Story")
    for task in tasks:
        for field in ("estimated_hours", "completed_hours", "remaining_hours"):
            value = task[field]
            if type(value) not in (int, float) or not isfinite(value) or value < 0:
                raise ValueError("Task hours must be finite nonnegative numbers")

    ordered = sorted(events, key=lambda e: (datetime.fromisoformat(e["timestamp"]), e["id"]))
    final_states = flow["daily_snapshots"][-1]["story_states"]
    rework_tasks = sorted((t for t in tasks if t["effort_kind"] == "rework"
                           and t["work_item_id"] in final_states), key=lambda t: t["id"])
    cycles = []
    stories = []
    for item_id, final_state in sorted(final_states.items()):
        item = items[item_id]
        if item["source"] not in ("roadmap", "client_incident"):
            raise ValueError("Unsupported v0.1 work source")
        history = [e for e in ordered if e["work_item_id"] == item_id]
        first_qa = None
        first_outcome = None
        first_outcome_event = None
        acceptance_ids = []
        story_cycles = []
        detections: dict[str, str] = {}
        resolutions: dict[str, str] = {}
        for event in history:
            before, after = event["from_state"], event["to_state"]
            bug_id = event.get("related_bug_id")
            if after == "QA" and before != "QA":
                if first_qa is None:
                    first_qa = event["id"]
                for cycle in story_cycles:
                    if cycle["status"] == "active":
                        cycle["qa_recertification_event_ids"].append(event["id"])
            if event["event_type"] == "bug_detected" and bug_id and before == "QA":
                detections[bug_id] = event["id"]
            if event["event_type"] == "bug_resolved" and bug_id:
                resolutions[bug_id] = event["id"]
            if before == "QA" and after == "Returned to DEV":
                if first_outcome is None:
                    first_outcome, first_outcome_event = "failed", event["id"]
                story_cycles.append({
                    "id": event["id"], "work_item_id": item_id,
                    "cycle_number": len(story_cycles) + 1,
                    "sprint_day": event["sprint_day"], "timestamp": event["timestamp"],
                    "related_bug_id": bug_id,
                    "qa_rejection_event_id": event["id"],
                    "bug_detection_event_id": detections.get(bug_id),
                    "return_to_dev_event_id": event["id"],
                    "qa_recertification_event_ids": [],
                    "acceptance_event_id": None, "status": "active",
                })
            if event["event_type"] == "qa_passed":
                if before != "QA" or after != "QA" or first_qa is None:
                    raise ValueError("QA acceptance needs a current QA attempt")
                acceptance_ids.append(event["id"])
                if first_outcome is None:
                    first_outcome, first_outcome_event = "passed", event["id"]
                for cycle in story_cycles:
                    if cycle["status"] == "active" and cycle["qa_recertification_event_ids"]:
                        cycle.update(status="completed", acceptance_event_id=event["id"])
        for cycle in story_cycles:
            bug_id = cycle["related_bug_id"]
            # Resolution evidence is separate from QA acceptance/cycle completion.
            cycle["bug_resolution_event_id"] = resolutions.get(bug_id)
            cycle["bug_resolution_status"] = (
                "resolved" if bug_id in resolutions else "unresolved"
            ) if bug_id else None
            cycle["bug_record_status"] = bug_index[bug_id]["status"] if bug_id else None
        reached = first_qa is not None
        eligible = item["source"] == "roadmap" and reached
        reason = None
        if item["source"] != "roadmap":
            outcome, reason = "excluded", "client_incident_excluded_in_v0.1"
        elif not reached:
            outcome, reason = "not_reached_qa", "no_qa_attempt_in_sprint"
        else:
            outcome = first_outcome
            if outcome is None:
                reason = "first_qa_attempt_has_no_recorded_outcome"
        stories.append({
            "work_item_id": item_id, "source": item["source"],
            "carry_over": item["carry_over"], "reached_qa": reached,
            "first_pass_population": eligible, "first_pass_outcome": outcome,
            "outcome_reason": reason, "final_state": final_state,
            "rework_cycles": len(story_cycles),
            "related_bugs": sorted({c["related_bug_id"] for c in story_cycles if c["related_bug_id"]}),
            "evidence": {"first_qa_event_id": first_qa,
                         "first_attempt_outcome_event_id": first_outcome_event,
                         "acceptance_event_ids": acceptance_ids},
            "rework_effort": _effort([t for t in rework_tasks if t["work_item_id"] == item_id]),
        })
        cycles.extend(story_cycles)
    eligible = [story for story in stories if story["first_pass_population"]]
    successes = sum(story["first_pass_outcome"] == "passed" for story in eligible)
    failures = sum(story["first_pass_outcome"] == "failed" for story in eligible)
    effort = _effort(rework_tasks)
    return {
        "sprint": flow["sprint"],
        "quality_summary": {
            "eligible_qa_stories": len(eligible), "first_pass_successes": successes,
            "first_pass_failures": failures,
            "first_pass_qa_rate": successes / len(eligible) if eligible else None,
            "stories_with_rework": sum(bool(s["rework_cycles"]) for s in stories),
            "total_rework_cycles": len(cycles),
            "active_rework_cycles_at_sprint_end": sum(c["status"] == "active" for c in cycles),
            "resolved_rework_cycles": sum(c["status"] == "completed" for c in cycles),
            "rework_bug_count": len({c["related_bug_id"] for c in cycles if c["related_bug_id"]}),
            "rework_task_count": effort["tasks"],
            **{f"rework_{field}": effort[field] for field in (
                "estimated_hours", "completed_hours", "remaining_hours",
            )},
        },
        "stories": stories, "rework_cycles": cycles, "rework_effort": effort,
    }
