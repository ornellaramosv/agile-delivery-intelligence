"""Quality expectations against frozen data and synthetic in-memory histories."""

from copy import deepcopy
import json

from fastapi.testclient import TestClient
import pytest

from app.domain.quality_rework import calculate_quality_rework
from app.main import app
from app.services.demo_quality_rework import SCENARIO_PATH


@pytest.fixture
def inputs():
    return {key: json.loads((SCENARIO_PATH / name).read_text()) for key, name in {
        "sprint": "sprint.json", "work_items": "work-items.json", "bugs": "bugs.json",
        "tasks": "tasks.json", "events": "delivery-events.json",
    }.items()}


@pytest.fixture
def result(inputs):
    return calculate_quality_rework(**inputs)


def story(result, item_id):
    return next(s for s in result["stories"] if s["work_item_id"] == item_id)


@pytest.mark.parametrize("item_id,outcome", [
    ("US-101", "passed"), ("US-102", "failed"), ("US-103", "passed"),
    ("US-104", "failed"), ("US-105", "failed"), ("US-106", "passed"),
    ("US-107", "not_reached_qa"), ("US-108", "not_reached_qa"),
    ("US-109", "not_reached_qa"), ("US-110", "passed"), ("US-111", "excluded"),
])
def test_per_story_outcomes(result, item_id, outcome):
    row = story(result, item_id)
    assert row["first_pass_outcome"] == outcome
    assert row["first_pass_population"] == (outcome in ("passed", "failed"))


def test_summary(result):
    assert result["quality_summary"] == {
        "eligible_qa_stories": 7, "first_pass_successes": 4, "first_pass_failures": 3,
        "first_pass_qa_rate": pytest.approx(4 / 7), "stories_with_rework": 3,
        "total_rework_cycles": 3, "active_rework_cycles_at_sprint_end": 1,
        "resolved_rework_cycles": 2, "rework_bug_count": 3,
        "rework_task_count": 7, "rework_estimated_hours": 45,
        "rework_completed_hours": 45, "rework_remaining_hours": 8,
    }


def test_opening_qa_and_carry_over_are_included(result):
    for n in range(101, 105):
        assert story(result, f"US-{n}")["evidence"]["first_qa_event_id"] == f"EVT-{n - 100:03d}"
    carry = story(result, "US-110")
    assert carry["carry_over"] and carry["first_pass_population"]
    assert carry["source"] == "roadmap"
    assert carry["evidence"]["first_qa_event_id"] == "EVT-011"
    excluded = story(result, "US-111")
    assert excluded["reached_qa"] and not excluded["first_pass_population"]
    assert excluded["outcome_reason"] == "client_incident_excluded_in_v0.1"


def test_closure_does_not_erase_failure_and_active_case_is_derived(result):
    for item_id in ("US-102", "US-105"):
        assert story(result, item_id)["final_state"] == "Closed"
        assert story(result, item_id)["first_pass_outcome"] == "failed"
    active = [c for c in result["rework_cycles"] if c["status"] == "active"]
    assert len(active) == 1
    assert active[0]["work_item_id"] == "US-104"
    assert active[0]["related_bug_id"] == "BUG-002"
    assert active[0]["bug_resolution_status"] == "unresolved"
    assert active[0]["acceptance_event_id"] is None
    assert story(result, "US-104")["final_state"] == "Returned to DEV"


def test_cycle_evidence(result):
    cycles = result["rework_cycles"]
    assert [c["return_to_dev_event_id"] for c in cycles] == ["EVT-015", "EVT-017", "EVT-028"]
    assert [c["bug_detection_event_id"] for c in cycles] == ["EVT-014", "EVT-016", "EVT-027"]
    assert [c["related_bug_id"] for c in cycles] == ["BUG-001", "BUG-002", "BUG-003"]
    assert [c["bug_resolution_event_id"] for c in cycles] == ["EVT-031", None, "EVT-045"]
    assert [c["acceptance_event_id"] for c in cycles] == ["EVT-030", None, "EVT-044"]
    assert [c["qa_recertification_event_ids"] for c in cycles] == [["EVT-026"], [], ["EVT-042"]]
    assert all(c["qa_rejection_event_id"] == c["return_to_dev_event_id"] for c in cycles)


@pytest.mark.parametrize("item_id,expected", [
    ("US-102", (3, 13, 15, 0)), ("US-104", (1, 16, 12, 8)),
    ("US-105", (3, 16, 18, 0)), ("US-111", (0, 0, 0, 0)),
])
def test_effort_per_story_preserves_overruns(result, item_id, expected):
    effort = story(result, item_id)["rework_effort"]
    assert tuple(effort[k] for k in ("tasks", "estimated_hours", "completed_hours", "remaining_hours")) == expected
    assert len(effort["task_ids"]) == expected[0]


def test_bug_and_task_existence_cannot_create_cycles(inputs, result):
    bug = deepcopy(inputs["bugs"][0])
    bug.update(id="BUG-EXTRA", work_item_id="US-108")
    inputs["bugs"].append(bug)
    task = deepcopy(inputs["tasks"][2])
    task.update(id="TASK-EXTRA", work_item_id="US-108", related_bug_id="BUG-EXTRA")
    inputs["tasks"].append(task)
    changed = calculate_quality_rework(**inputs)
    assert changed["rework_cycles"] == result["rework_cycles"]
    assert changed["quality_summary"]["rework_bug_count"] == 3
    assert changed["quality_summary"]["rework_task_count"] == 8
    assert story(changed, "US-108")["rework_cycles"] == 0


def test_effort_uses_classification_not_task_type(inputs, result):
    inputs["tasks"][0]["type"] = "Bug Fix"
    inputs["tasks"][0]["completed_hours"] = 500
    assert calculate_quality_rework(**inputs) == result
    inputs["tasks"][2]["effort_kind"] = "planned"
    changed = calculate_quality_rework(**inputs)
    assert changed["quality_summary"]["rework_task_count"] == 6
    assert changed["quality_summary"]["total_rework_cycles"] == 3


def test_acceptance_not_closed_snapshot_is_required(inputs):
    inputs["events"] = [e for e in inputs["events"] if not (
        e["work_item_id"] == "US-101" and e["event_type"] == "qa_passed")]
    row = story(calculate_quality_rework(**inputs), "US-101")
    assert row["final_state"] == "Closed"
    assert row["first_pass_outcome"] is None
    assert row["first_pass_population"]


def test_bug_resolution_alone_does_not_complete_cycle(inputs):
    inputs["events"] = [e for e in inputs["events"] if e["id"] != "EVT-030"]
    cycle = calculate_quality_rework(**inputs)["rework_cycles"][0]
    assert cycle["status"] == "active"
    assert cycle["bug_resolution_status"] == "resolved"


def test_missing_bug_link_does_not_erase_workflow_rework(inputs):
    next(e for e in inputs["events"] if e["id"] == "EVT-015")["related_bug_id"] = None
    result = calculate_quality_rework(**inputs)
    assert result["quality_summary"]["total_rework_cycles"] == 3
    assert result["rework_cycles"][0]["related_bug_id"] is None
    assert result["rework_cycles"][0]["bug_resolution_status"] is None


def test_determinism_nonmutation_and_final_snapshots_ignored(inputs, result):
    original = deepcopy(inputs)
    assert calculate_quality_rework(**inputs) == result
    assert inputs == original
    for key in ("work_items", "events", "tasks", "bugs"):
        inputs[key].reverse()
    for item in inputs["work_items"]:
        item["state"] = "Blocked"
    assert calculate_quality_rework(**inputs) == result


def test_multiple_cycles_one_story_without_fixture_changes(inputs):
    # US-104 returns to QA, fails again, then recertifies and passes.
    def event(event_id, day, before, after, event_type):
        date = inputs["sprint"]["working_days"][day - 1]["date"]
        return {"id": event_id, "work_item_id": "US-104", "sprint_day": day,
                "timestamp": f"{date}T16:00:00Z", "from_state": before,
                "to_state": after, "event_type": event_type, "related_bug_id": "BUG-002"}
    inputs["events"].extend([
        event("SYN-1", 5, "Returned to DEV", "QA", "entered_qa"),
        event("SYN-2", 6, "QA", "Returned to DEV", "returned_to_dev"),
        event("SYN-3", 7, "Returned to DEV", "QA", "entered_qa"),
        event("SYN-4", 8, "QA", "QA", "bug_resolved"),
        event("SYN-5", 9, "QA", "QA", "qa_passed"),
    ])
    result = calculate_quality_rework(**inputs)
    row = story(result, "US-104")
    assert row["rework_cycles"] == 2
    assert row["first_pass_outcome"] == "failed"
    cycles = [c for c in result["rework_cycles"] if c["work_item_id"] == "US-104"]
    assert [c["cycle_number"] for c in cycles] == [1, 2]
    assert all(c["status"] == "completed" for c in cycles)
    assert result["quality_summary"]["total_rework_cycles"] == 4
    assert result["quality_summary"]["stories_with_rework"] == 3
    assert result["quality_summary"]["rework_bug_count"] == 3


def test_empty_eligible_population_has_no_rate(inputs):
    for item in inputs["work_items"]:
        item["source"] = "client_incident"
    summary = calculate_quality_rework(**inputs)["quality_summary"]
    assert summary["eligible_qa_stories"] == 0
    assert summary["first_pass_qa_rate"] is None


@pytest.mark.parametrize("kind", ["bad_bug_link", "bad_task_link", "duplicate_task", "negative_hours"])
def test_invalid_evidence_rejected(inputs, kind):
    if kind == "bad_bug_link":
        inputs["bugs"][0]["work_item_id"] = "US-101"
    elif kind == "bad_task_link":
        inputs["tasks"][0]["work_item_id"] = "UNKNOWN"
    elif kind == "duplicate_task":
        inputs["tasks"].append(deepcopy(inputs["tasks"][0]))
    else:
        inputs["tasks"][0]["remaining_hours"] = -1
    with pytest.raises(ValueError):
        calculate_quality_rework(**inputs)


def test_api_matches_direct_engine(result):
    with TestClient(app) as client:
        response = client.get("/demo/sprint-08/quality-rework")
    assert response.status_code == 200
    assert response.json() == result


def test_roadmap_scope_addition_is_eligible(inputs):
    next(item for item in inputs["work_items"] if item["id"] == "US-111")["source"] = "roadmap"
    result = calculate_quality_rework(**inputs)
    assert story(result, "US-111")["first_pass_outcome"] == "passed"
    assert result["quality_summary"]["eligible_qa_stories"] == 8


def test_independent_of_fixture_story_ids(inputs, result):
    mapping = {item["id"]: f"STORY-{index}" for index, item in enumerate(inputs["work_items"])}
    for item in inputs["work_items"]:
        item["id"] = mapping[item["id"]]
    for key in ("bugs", "tasks", "events"):
        for record in inputs[key]:
            record["work_item_id"] = mapping[record["work_item_id"]]
    inputs["sprint"]["original_baseline_work_item_ids"] = [
        mapping[item_id] for item_id in inputs["sprint"]["original_baseline_work_item_ids"]]
    assert calculate_quality_rework(**inputs)["quality_summary"] == result["quality_summary"]
