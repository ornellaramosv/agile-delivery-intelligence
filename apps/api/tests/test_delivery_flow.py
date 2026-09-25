"""Frozen-fixture expectations and in-memory event variations."""

from copy import deepcopy
import json

from fastapi.testclient import TestClient
import pytest

from app.domain.delivery_flow import WORKFLOW_STATES, calculate_delivery_flow
from app.main import app
from app.services.demo_delivery_flow import SCENARIO_PATH


@pytest.fixture
def inputs():
    return {key: json.loads((SCENARIO_PATH / filename).read_text()) for key, filename in {
        "sprint": "sprint.json", "work_items": "work-items.json",
        "events": "delivery-events.json",
    }.items()}


@pytest.fixture
def result(inputs):
    return calculate_delivery_flow(**inputs)


def test_all_daily_distributions(result, inputs):
    expected = [
        [5, 0, 1, 4, 0, 0, 0], [5, 0, 0, 4, 0, 0, 1],
        [5, 0, 0, 3, 1, 0, 1], [4, 1, 0, 2, 2, 0, 1],
        [4, 0, 1, 2, 2, 0, 1], [5, 0, 1, 2, 1, 0, 2],
        [4, 1, 0, 1, 2, 0, 3], [3, 1, 1, 0, 2, 0, 4],
        [3, 0, 1, 2, 1, 0, 4], [2, 1, 0, 0, 1, 0, 7],
    ]
    assert result["workflow_states"] == list(WORKFLOW_STATES)
    assert [list(d["states"].values()) for d in result["daily_snapshots"]] == expected
    assert [{"sprint_day": d["sprint_day"], "date": d["date"]}
            for d in result["daily_snapshots"]] == inputs["sprint"]["working_days"]


def test_scope_and_exactly_once_counting(result):
    for day in result["daily_snapshots"]:
        expected_ids = {f"US-{n}" for n in range(101, 111 + (day["sprint_day"] >= 6))}
        assert set(day["story_states"]) == expected_ids
        assert day["total_active_scope"] == len(expected_ids)
        assert day["open_stories"] + day["closed_stories"] == len(expected_ids)
        assert sum(day["states"].values()) == len(expected_ids)
        for state in WORKFLOW_STATES:
            assert day["states"][state] == list(day["story_states"].values()).count(state)
    assert all(m["work_item_id"] != "US-111" for d in result["daily_movements"][:5]
               for m in d["movements"] + d["scope_entries"])


@pytest.mark.parametrize("item_id,expected", [
    ("US-102", ["QA", "Returned to DEV", "Code Integration", "Ready for QA", "QA", "Closed"]),
    ("US-105", ["Development", "Code Integration", "Ready for QA", "QA",
                "Returned to DEV", "Code Integration", "Ready for QA", "QA", "Closed"]),
])
def test_traceable_rework_paths(result, item_id, expected):
    entry = next(e for d in result["daily_movements"] for e in d["scope_entries"]
                 if e["work_item_id"] == item_id)
    path = [entry["to_state"]] + [m["to_state"] for d in result["daily_movements"]
                                  for m in d["movements"] if m["work_item_id"] == item_id]
    assert path == expected


@pytest.mark.parametrize("item_id,state", [
    ("US-104", "Returned to DEV"), ("US-107", "Code Integration"),
    ("US-108", "Development"), ("US-109", "Development"),
])
def test_open_final_states(result, item_id, state):
    assert result["daily_snapshots"][-1]["story_states"][item_id] == state


def test_closed_final_stories(result):
    final = result["daily_snapshots"][-1]
    assert {key for key, value in final["story_states"].items() if value == "Closed"} == {
        "US-101", "US-102", "US-103", "US-105", "US-106", "US-110", "US-111",
    }
    assert (final["open_stories"], final["closed_stories"], final["total_active_scope"]) == (4, 7, 11)


def test_context_events_do_not_change_result(inputs, result):
    inputs["events"] = [e for e in inputs["events"] if e["from_state"] != e["to_state"]]
    assert calculate_delivery_flow(**inputs) == result
    context = deepcopy(inputs["events"][0])
    context.update(id="CONTEXT", event_type="note", from_state=None, to_state=None,
                   timestamp="2030-04-08T17:00:00Z")
    inputs["events"].append(context)
    assert calculate_delivery_flow(**inputs) == result


def test_movements_are_exactly_actual_transitions(inputs, result):
    expected = {e["id"] for e in inputs["events"]
                if e["from_state"] is not None and e["from_state"] != e["to_state"]}
    actual = [m for d in result["daily_movements"] for m in d["movements"]]
    assert {m["event_id"] for m in actual} == expected
    assert len(actual) == len(expected)
    for day in result["daily_movements"]:
        assert day["movements"] == sorted(day["movements"], key=lambda m: (m["timestamp"], m["event_id"]))
        assert all(m["from_state"] in WORKFLOW_STATES and m["to_state"] in WORKFLOW_STATES
                   and m["from_state"] != m["to_state"] for m in day["movements"])


def test_opening_events_and_formal_scope_entry(result):
    days = result["daily_movements"]
    assert len(days[0]["scope_entries"]) == 10
    assert days[0]["movements"] == []
    assert [e["work_item_id"] for e in days[5]["scope_entries"]] == ["US-111"]
    assert sum(len(d["scope_entries"]) for d in days) == 11


def test_deterministic_non_mutating_replay(inputs, result):
    original = deepcopy(inputs)
    assert calculate_delivery_flow(**inputs) == result
    assert inputs == original
    inputs["events"].reverse()
    inputs["work_items"].reverse()
    assert calculate_delivery_flow(**inputs) == result


def test_final_item_snapshots_are_not_a_state_source(inputs, result):
    for item in inputs["work_items"]:
        item["state"] = "Blocked"
    assert calculate_delivery_flow(**inputs) == result


def test_changed_event_changes_snapshot_without_hardcoded_counts(inputs):
    # In-memory variation: US-108 reaches Blocked on Day 2.
    inputs["events"].append({
        "id": "VARIATION", "work_item_id": "US-108", "event_type": "state_changed",
        "from_state": "Development", "to_state": "Blocked", "sprint_day": 2,
        "timestamp": "2030-04-09T17:00:00Z",
    })
    days = calculate_delivery_flow(**inputs)["daily_snapshots"]
    assert days[0]["states"]["Blocked"] == 0
    assert all(d["states"]["Blocked"] == 1 and d["story_states"]["US-108"] == "Blocked"
               for d in days[1:])
    assert days[-1]["states"]["Development"] == 1


def test_scope_activation_uses_event_day(inputs):
    entry = next(e for e in inputs["events"] if e["event_type"] == "scope_added")
    entry.update(sprint_day=7, timestamp="2030-04-16T09:30:00Z")
    days = calculate_delivery_flow(**inputs)["daily_snapshots"]
    assert [d["total_active_scope"] for d in days] == [10] * 6 + [11] * 4


@pytest.mark.parametrize("mutation", ["missing_opening", "duplicate", "unknown_item",
                                      "unknown_state", "broken_history", "wrong_date"])
def test_invalid_histories_are_rejected(inputs, mutation):
    if mutation == "missing_opening":
        inputs["events"] = [e for e in inputs["events"] if e["work_item_id"] != "US-108"]
    elif mutation == "duplicate":
        inputs["events"].append(deepcopy(inputs["events"][0]))
    elif mutation == "unknown_item":
        inputs["events"][0]["work_item_id"] = "UNKNOWN"
    elif mutation == "unknown_state":
        inputs["events"][0]["to_state"] = "Done"
    elif mutation == "broken_history":
        next(e for e in inputs["events"] if e["event_type"] == "returned_to_dev")["from_state"] = "Closed"
    else:
        inputs["events"][0]["timestamp"] = "2030-04-09T09:00:00Z"
    with pytest.raises(ValueError):
        calculate_delivery_flow(**inputs)


def test_api_matches_domain(result):
    with TestClient(app) as client:
        response = client.get("/demo/sprint-08/delivery-flow")
    assert response.status_code == 200
    assert response.json() == result
