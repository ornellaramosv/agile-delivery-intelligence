"""Fixture assertions and in-memory variations; never modify frozen records."""

from copy import deepcopy
import json

from fastapi.testclient import TestClient
import pytest

from app.domain.burndown import BurndownConfig, calculate_burndown
from app.main import app
from app.services.demo_burndown import SCENARIO_PATH


@pytest.fixture
def inputs():
    files = {"sprint": "sprint.json", "work_items": "work-items.json",
             "bugs": "bugs.json", "events": "delivery-events.json"}
    return {key: json.loads((SCENARIO_PATH / name).read_text()) for key, name in files.items()}


@pytest.fixture
def result(inputs):
    return calculate_burndown(**inputs)


def flatlines(result):
    return [i for i in result["insights"] if i["type"] == "flatline"]


def test_daily_series_and_immutable_baseline(result):
    days = result["daily_snapshots"]
    assert [d["current_remaining_work"] for d in days] == [10, 9, 10, 11, 11, 11, 10, 9, 9, 5]
    assert [d["original_baseline"] for d in days] == [10] * 10
    assert [d["sprint_day"] for d in days] == list(range(1, 11))
    assert [d["closed_baseline_stories"] for d in days] == [0, 1, 1, 1, 1, 2, 3, 4, 4, 6]


def test_scope_contribution_starts_at_entry_and_ends_at_closure(result):
    days = result["daily_snapshots"]
    assert [d["open_scope_added_stories"] for d in days] == [0] * 5 + [1] * 4 + [0]
    assert [d["scope_added_total"] for d in days] == [0] * 5 + [1] * 5
    assert [d["closed_scope_added_stories"] for d in days] == [0] * 9 + [1]
    assert all("US-111" not in d["composition"]["open_baseline_story_ids"] for d in days)


@pytest.mark.parametrize("bug_id,days_open", [
    ("BUG-001", {3, 4, 5, 6}), ("BUG-002", set(range(4, 11))), ("BUG-003", {7, 8, 9}),
])
def test_bug_lifetimes(result, bug_id, days_open):
    assert {d["sprint_day"] for d in result["daily_snapshots"]
            if bug_id in d["composition"]["open_closure_blocking_bug_ids"]} == days_open
    assert {d["sprint_day"] for d in result["daily_snapshots"]
            if bug_id in d["active_rework_bugs"]} == days_open


def test_closed_stories_removed_and_qa_rejection_not_double_counted(result):
    for d in result["daily_snapshots"]:
        baseline = d["composition"]["open_baseline_story_ids"]
        assert len(baseline) == len(set(baseline)) == d["open_baseline_stories"]
        assert d["open_baseline_stories"] + d["closed_baseline_stories"] == 10
        assert d["current_remaining_work"] == (d["open_baseline_stories"]
                + d["open_scope_added_stories"] + d["open_closure_blocking_bugs"])
        if d["sprint_day"] >= 2:
            assert "US-101" not in baseline
    d = result["daily_snapshots"][2]
    assert (d["open_baseline_stories"], d["current_remaining_work"]) == (9, 10)
    assert [c["type"] for c in d["explanation"]["causes"]] == ["closure_blocking_bug_created"]


def test_deltas_and_causes_reconcile(result):
    days = result["daily_snapshots"]
    assert days[0]["explanation"] == {"day": 1, "movement": None, "delta": None, "causes": []}
    for previous, current in zip(days, days[1:]):
        explanation = current["explanation"]
        delta = current["current_remaining_work"] - previous["current_remaining_work"]
        assert explanation["delta"] == delta
        assert sum(c["effect"] for c in explanation["causes"]) == delta
        assert explanation["movement"] == ("up" if delta > 0 else "down" if delta < 0 else "flat")
        assert all(c["event_id"] and c["timestamp"] for c in explanation["causes"])


def test_flat_day_preserves_opposing_causes(result):
    explanation = result["daily_snapshots"][5]["explanation"]
    assert (explanation["movement"], explanation["delta"]) == ("flat", 0)
    assert [(c["type"], c["id"], c["effect"]) for c in explanation["causes"]] == [
        ("scope_added", "US-111", 1), ("story_closed", "US-110", -1),
    ]


def test_upward_insights(result):
    upward = [i for i in result["insights"] if i["type"] == "upward_movement"]
    assert [(i["sprint_day"], i["previous_remaining"], i["current_remaining"], i["delta"])
            for i in upward] == [(3, 9, 10, 1), (4, 10, 11, 1)]
    assert [i["causes"][0]["id"] for i in upward] == ["BUG-001", "BUG-002"]
    assert all(i["causes"][0]["type"] == "closure_blocking_bug_created" for i in upward)


def test_flatline_and_context(result):
    assert result["configuration"]["flatline_threshold_days"] == 2
    insight, = flatlines(result)
    assert (insight["start_day"], insight["end_day"], insight["number_of_days"], insight["remaining_work"]) == (5, 6, 2, 11)
    assert insight["contributing_context"][0]["event_ids"] == ["EVT-019"]
    assert len(insight["contributing_context"][1]["causes"]) == 2


def test_confirmed_day_three_to_six_classifications_exclude_upward_days(result):
    days = result["daily_snapshots"][2:6]
    assert [(day["sprint_day"], day["explanation"]["delta"], day["explanation"]["movement"])
            for day in days] == [(3, 1, "up"), (4, 1, "up"), (5, 0, "flat"), (6, 0, "flat")]
    flatline_days = {
        day for insight in flatlines(result)
        for day in range(insight["start_day"], insight["end_day"] + 1)
    }
    assert flatline_days == {5, 6}
    assert flatline_days.isdisjoint({3, 4})


def test_upward_day_breaks_two_flat_runs(inputs):
    # In-memory variant: flat on Days 2–3, scope addition on Day 4, then flat again.
    baseline = inputs["work_items"][0]
    added = next(item for item in inputs["work_items"] if item["id"] == "US-111")
    opening = inputs["events"][0]
    addition = next(event for event in inputs["events"] if event["event_type"] == "scope_added")
    addition.update(sprint_day=4, timestamp="2030-04-11T09:30:00Z")
    inputs["work_items"] = [baseline, added]
    inputs["sprint"]["original_baseline_work_item_ids"] = [baseline["id"]]
    inputs["bugs"] = []
    inputs["events"] = [opening, addition]

    result = calculate_burndown(**inputs)
    assert result["daily_snapshots"][3]["explanation"]["movement"] == "up"
    assert [(i["start_day"], i["end_day"], i["number_of_days"]) for i in flatlines(result)] == [
        (2, 3, 2), (5, 10, 6),
    ]


@pytest.mark.parametrize("threshold,expected", [(1, [(5, 6), (9, 9)]), (2, [(5, 6)]), (3, [])])
def test_configurable_threshold(inputs, threshold, expected):
    result = calculate_burndown(**inputs, config=BurndownConfig(threshold))
    assert result["configuration"]["flatline_threshold_days"] == threshold
    assert [(i["start_day"], i["end_day"]) for i in flatlines(result)] == expected


@pytest.mark.parametrize("threshold", [0, -1, 1.5, True, "2"])
def test_invalid_threshold(threshold):
    with pytest.raises(ValueError, match="positive integer"):
        BurndownConfig(threshold)


def test_final_composition(result):
    final = result["daily_snapshots"][-1]
    assert final["current_remaining_work"] == 5
    assert final["composition"] == {
        "open_baseline_story_ids": ["US-104", "US-107", "US-108", "US-109"],
        "open_scope_added_story_ids": [], "open_closure_blocking_bug_ids": ["BUG-002"],
    }
    assert final["active_rework_bugs"] == ["BUG-002"]


def test_determinism_nonmutation_and_event_order(inputs):
    before = deepcopy(inputs)
    expected = calculate_burndown(**inputs)
    assert calculate_burndown(**inputs) == expected
    assert inputs == before
    inputs["events"].reverse()
    assert calculate_burndown(**inputs) == expected


def test_final_states_and_legacy_blocking_are_not_calculation_inputs(inputs):
    expected = calculate_burndown(**inputs)
    for item in inputs["work_items"]:
        item["state"] = "Closed"
    for bug in inputs["bugs"]:
        bug["status"] = "Open"
        bug["blocking"] = not bug["blocking"]
    assert calculate_burndown(**inputs) == expected


def test_non_closure_blocking_bug_adds_no_unit(inputs):
    inputs["bugs"][0]["blocks_story_closure"] = False
    result = calculate_burndown(**inputs)
    assert result["daily_snapshots"][2]["current_remaining_work"] == 9
    assert "BUG-001" in result["daily_snapshots"][2]["active_rework_bugs"]
    assert all(c["id"] != "BUG-001" for d in result["daily_snapshots"] for c in d["explanation"]["causes"])


def test_scope_timing_comes_from_event(inputs):
    event = next(e for e in inputs["events"] if e["event_type"] == "scope_added")
    event.update(sprint_day=5, timestamp="2030-04-12T09:30:00Z")
    days = calculate_burndown(**inputs)["daily_snapshots"]
    assert days[3]["scope_added_total"] == 0
    assert (days[4]["open_scope_added_stories"], days[4]["current_remaining_work"]) == (1, 12)


def test_independent_of_fixture_ids(inputs):
    expected = calculate_burndown(**inputs)
    mapping = {r["id"]: f"fictional-{i}" for i, r in enumerate(inputs["work_items"] + inputs["bugs"])}
    inputs["sprint"]["original_baseline_work_item_ids"] = [mapping[k] for k in inputs["sprint"]["original_baseline_work_item_ids"]]
    for r in inputs["work_items"] + inputs["bugs"] + inputs["events"]:
        for field in ("id", "work_item_id", "related_bug_id"):
            if r.get(field) in mapping:
                r[field] = mapping[r[field]]
    result = calculate_burndown(**inputs)
    assert [d["current_remaining_work"] for d in result["daily_snapshots"]] == [d["current_remaining_work"] for d in expected["daily_snapshots"]]


def test_same_day_bug_creation_and_resolution_retains_both_causes(inputs):
    bug = inputs["bugs"][0]
    bug["resolved_at"] = "2030-04-10T10:03:00Z"
    inputs["events"] = [e for e in inputs["events"] if e["related_bug_id"] != "BUG-001" or e["event_type"] == "bug_detected"]
    inputs["events"].append({"id": "same-day-resolution", "work_item_id": "US-102",
        "event_type": "bug_resolved", "from_state": "QA", "to_state": "QA",
        "sprint_day": 3, "timestamp": bug["resolved_at"], "related_bug_id": "BUG-001"})
    day = calculate_burndown(**inputs)["daily_snapshots"][2]
    assert day["explanation"]["movement"] == "flat"
    assert [c["effect"] for c in day["explanation"]["causes"]] == [1, -1]
    assert day["open_closure_blocking_bugs"] == 0


def test_flatline_at_horizon_excludes_day_one(inputs):
    item = inputs["work_items"][0]
    inputs["work_items"] = [item]
    inputs["sprint"]["original_baseline_work_item_ids"] = [item["id"]]
    inputs["bugs"] = []
    inputs["events"] = [inputs["events"][0]]
    insight, = flatlines(calculate_burndown(**inputs))
    assert (insight["start_day"], insight["end_day"], insight["number_of_days"]) == (2, 10, 9)
    assert insight["remaining_work"] == 1


def test_missing_bug_lifecycle_evidence_rejected(inputs):
    inputs["events"] = [e for e in inputs["events"] if e["event_type"] != "bug_resolved"]
    with pytest.raises(ValueError):
        calculate_burndown(**inputs)


def test_demo_endpoint_equals_direct_engine(inputs):
    with TestClient(app) as client:
        response = client.get("/demo/sprint-08/burndown")
    assert response.status_code == 200
    assert response.json() == calculate_burndown(**inputs)
