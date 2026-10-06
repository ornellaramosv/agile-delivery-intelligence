"""Validate the fictional fixture, not application analytics or metric formulas."""

import hashlib
import json
import math
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path


SCENARIO = Path(__file__).resolve().parents[1] / "demo" / "sprint-08"
# Frozen v1 content; update only for a Product Owner-approved dataset defect.
FROZEN_V1_SHA256 = {
    "bugs.json": "c92f614bf084b2c4a218745917577e24ee037e8a3f3af4cf140aca3b66cb81df",
    "delivery-events.json": "e9299edec31043dc4a1732396c8b3be8c35df580be76426f34b08709fee459b1",
    "sprint.json": "2f119f4f95a553042e81d31435847849f01ae0ef3a0c137e5662c9a667483dc0",
    "tasks.json": "0e41717d4ad342f579e35fe70e770a7b596582506131396d59b125e22c08ca7a",
    "work-items.json": "4c4115def72a4bf8ba8d76932637ba7749bcea43d5c377ec71b166c88997c410"
}
STATES = {
    "Development", "Code Integration", "Ready for QA", "QA",
    "Returned to DEV", "Blocked", "Closed",
}
TASK_TYPES = {
    "Development", "Code Review / Integration", "QA Certification",
    "Bug Fix", "QA Recertification",
}
SOURCES = {"roadmap", "client_incident"}
EFFORT_KINDS = {"planned", "rework", "scope_added"}
BUG_LINKS = {"BUG-001": "US-102", "BUG-002": "US-104", "BUG-003": "US-105"}
CLOSED_DAYS = {
    "US-101": 2, "US-102": 7, "US-103": 8, "US-105": 10,
    "US-106": 10, "US-110": 6, "US-111": 10,
}
OPEN_STATES = {
    "US-104": "Returned to DEV", "US-107": "Code Integration",
    "US-108": "Development", "US-109": "Development",
}


def load(filename):
    return json.loads((SCENARIO / filename).read_text(encoding="utf-8"))


class Sprint08Validation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sprint = load("sprint.json")
        cls.items = load("work-items.json")
        cls.tasks = load("tasks.json")
        cls.bugs = load("bugs.json")
        cls.events = load("delivery-events.json")
        cls.item_by_id = {item["id"]: item for item in cls.items}
        cls.bug_by_id = {bug["id"]: bug for bug in cls.bugs}
        cls.calendar = {
            entry["sprint_day"]: entry["date"] for entry in cls.sprint["working_days"]
        }

    def events_for(self, item_id, event_type=None):
        return [
            event for event in self.events
            if event["work_item_id"] == item_id
            and (event_type is None or event["event_type"] == event_type)
        ]

    def assert_timestamp(self, value):
        parsed = datetime.fromisoformat(value)
        self.assertEqual(parsed.utcoffset(), timedelta(0), value)
        self.assertIn(parsed.date().isoformat(), self.calendar.values(), value)
        self.assertGreaterEqual(parsed, datetime.fromisoformat(self.sprint["baseline_at"]))
        self.assertLessEqual(parsed, datetime.fromisoformat(self.sprint["snapshot_at"]))
        return parsed

    def test_unique_ids_and_required_fields(self):
        fields = (
            (self.items, {"id", "title", "backlog", "type", "state", "source",
                          "original_baseline", "scope_added_after_baseline", "carry_over"}),
            (self.tasks, {"id", "work_item_id", "title", "type", "effort_kind",
                          "estimated_hours", "completed_hours", "remaining_hours",
                          "state", "created_at", "completed_at", "related_bug_id"}),
            (self.bugs, {"id", "work_item_id", "created_at", "resolved_at", "status", "blocking", "blocks_story_closure"}),
            (self.events, {"id", "work_item_id", "event_type", "from_state", "to_state",
                           "sprint_day", "timestamp", "related_bug_id", "description"}),
        )
        for records, required in fields:
            self.assertEqual(len(records), len({record["id"] for record in records}))
            for record in records:
                with self.subTest(record=record["id"]):
                    self.assertTrue(required <= record.keys())
                    self.assertIsInstance(record["id"], str)

    def test_all_foreign_keys(self):
        for record in self.tasks + self.bugs + self.events:
            with self.subTest(record=record["id"]):
                self.assertIn(record["work_item_id"], self.item_by_id)
                if record.get("related_bug_id") is not None:
                    self.assertIn(record["related_bug_id"], self.bug_by_id)
                    self.assertEqual(
                        record["work_item_id"],
                        self.bug_by_id[record["related_bug_id"]]["work_item_id"],
                    )

    def test_frozen_v1_scenario_content(self):
        # v0.2 adds separate evidence files; the five v1 digests remain unchanged.
        capacity_files = {
            "capacity-plan.json", "capacity-ledger.json", "task-capacity-map.json",
            "dependencies.json", "scope-decisions.json", "release-regression.json",
        }
        self.assertEqual({path.name for path in SCENARIO.glob("*.json")},
                         set(FROZEN_V1_SHA256) | capacity_files)
        for filename, expected in FROZEN_V1_SHA256.items():
            with self.subTest(file=filename):
                canonical = json.dumps(
                    load(filename), sort_keys=True, separators=(",", ":"), ensure_ascii=False
                ).encode("utf-8")
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), expected)

    def test_explicit_story_closure_flags_and_preserved_blocking_flags(self):
        self.assertEqual(set(self.bug_by_id), set(BUG_LINKS))
        for bug in self.bugs:
            with self.subTest(bug=bug["id"]):
                self.assertIn("blocks_story_closure", bug)
                self.assertIsInstance(bug["blocks_story_closure"], bool)
                self.assertIs(bug["blocks_story_closure"], True)
                self.assertIs(bug["blocking"], bug["id"] == "BUG-002")
                self.assertEqual(bug["work_item_id"], BUG_LINKS[bug["id"]])

    def test_story_acceptance_follows_resolution_of_closure_blocking_bug(self):
        for bug in self.bugs:
            if bug["blocks_story_closure"]:
                closures = self.events_for(bug["work_item_id"], "closed")
                if bug["resolved_at"] is None:
                    self.assertEqual(closures, [])
                else:
                    for closure in closures:
                        self.assertGreaterEqual(closure["timestamp"], bug["resolved_at"])

    def test_immutable_baseline_membership_and_flags(self):
        baseline = {f"US-{number}" for number in range(101, 111)}
        self.assertEqual(set(self.item_by_id), baseline | {"US-111"})
        self.assertEqual(len(self.sprint["original_baseline_work_item_ids"]), 10)
        self.assertEqual(set(self.sprint["original_baseline_work_item_ids"]), baseline)
        self.assertEqual({item["id"] for item in self.items if item["original_baseline"]}, baseline)
        self.assertEqual(
            [item["id"] for item in self.items if item["scope_added_after_baseline"]], ["US-111"]
        )
        self.assertEqual([item["id"] for item in self.items if item["carry_over"]], ["US-110"])
        for item in self.items:
            self.assertEqual(item["type"], "User Story")
            self.assertEqual(item["backlog"], "Core Services")
            for field in ("original_baseline", "scope_added_after_baseline", "carry_over"):
                self.assertIsInstance(item[field], bool)
            self.assertNotEqual(item["original_baseline"], item["scope_added_after_baseline"])

    def test_calendar_and_all_timestamps(self):
        self.assertEqual(self.sprint["project"], "Atlas")
        self.assertEqual(self.sprint["name"], "Sprint 08")
        self.assertEqual(self.sprint["timezone"], "UTC")
        self.assertEqual(len(self.sprint["working_days"]), 10)
        self.assertEqual(list(self.calendar), list(range(1, 11)))
        start = date.fromisoformat(self.sprint["start_date"])
        self.assertEqual(start.weekday(), 0)
        dates = [start + timedelta(days=i) for i in range(12) if i % 7 < 5]
        self.assertEqual(list(self.calendar.values()), [day.isoformat() for day in dates])
        self.assertEqual(self.sprint["end_date"], dates[-1].isoformat())
        for record in self.tasks + self.bugs + self.events:
            for field in ("created_at", "completed_at", "resolved_at", "timestamp"):
                if record.get(field) is not None:
                    with self.subTest(record=record["id"], field=field):
                        parsed = self.assert_timestamp(record[field])
                        if field == "timestamp":
                            self.assertEqual(parsed.date().isoformat(), self.calendar[record["sprint_day"]])

    def test_normalized_states(self):
        for record in self.items + self.tasks:
            self.assertIn(record["state"], STATES, record["id"])
        for event in self.events:
            self.assertIn(event["to_state"], STATES, event["id"])
            if event["from_state"] is not None:
                self.assertIn(event["from_state"], STATES, event["id"])
            else:
                self.assertIn(event["event_type"], {"sprint_started", "scope_added"})

    def test_history_continuity_matches_final_snapshot(self):
        timestamps = [event["timestamp"] for event in self.events]
        self.assertEqual(timestamps, sorted(timestamps))
        for item in self.items:
            state = None
            history = self.events_for(item["id"])
            self.assertTrue(history, item["id"])
            self.assertIsNone(history[0]["from_state"])
            for index, event in enumerate(history):
                with self.subTest(event=event["id"]):
                    self.assertEqual(event["from_state"], state)
                    if index:
                        self.assertIsNotNone(event["from_state"])
                    state = event["to_state"]
            self.assertEqual(state, item["state"], item["id"])

    def test_opening_states(self):
        for number in range(101, 111):
            event = self.events_for(f"US-{number}")[0]
            expected = "QA" if number <= 104 else "Ready for QA" if number == 110 else "Development"
            self.assertEqual(event["event_type"], "sprint_started")
            self.assertEqual(event["timestamp"], self.sprint["baseline_at"])
            self.assertEqual(event["to_state"], expected)

    def test_day_six_scope_addition(self):
        additions = [event for event in self.events if event["event_type"] == "scope_added"]
        self.assertEqual(len(additions), 1)
        event = additions[0]
        self.assertEqual(event["work_item_id"], "US-111")
        self.assertEqual(event["sprint_day"], 6)
        self.assertEqual(self.events_for("US-111")[0], event)
        self.assertEqual(self.item_by_id["US-111"]["source"], "client_incident")
        for item in self.items:
            if item["id"] != "US-111":
                self.assertEqual(item["source"], "roadmap")
        for task in self.tasks:
            if task["work_item_id"] == "US-111":
                self.assertGreaterEqual(task["created_at"], event["timestamp"])

    def test_final_states_and_closure_days(self):
        expected = {**{item_id: "Closed" for item_id in CLOSED_DAYS}, **OPEN_STATES}
        self.assertEqual({item["id"]: item["state"] for item in self.items}, expected)
        for item_id in expected:
            closures = self.events_for(item_id, "closed")
            if item_id in CLOSED_DAYS:
                self.assertEqual(len(closures), 1)
                self.assertEqual(closures[0]["sprint_day"], CLOSED_DAYS[item_id])
                self.assertEqual((closures[0]["from_state"], closures[0]["to_state"]), ("QA", "Closed"))
            else:
                self.assertEqual(closures, [])

    def test_bug_links_and_lifecycles(self):
        self.assertEqual({bug["id"]: bug["work_item_id"] for bug in self.bugs}, BUG_LINKS)
        for bug_id, day, resolved_day in [("BUG-001", 3, 7), ("BUG-002", 4, None), ("BUG-003", 7, 10)]:
            bug = self.bug_by_id[bug_id]
            detections = self.events_for(bug["work_item_id"], "bug_detected")
            resolutions = self.events_for(bug["work_item_id"], "bug_resolved")
            self.assertEqual(len(detections), 1)
            self.assertEqual(detections[0]["related_bug_id"], bug_id)
            self.assertEqual(detections[0]["sprint_day"], day)
            self.assertEqual(detections[0]["timestamp"], bug["created_at"])
            if resolved_day is None:
                self.assertEqual(bug["status"], "Open")
                self.assertIsNone(bug["resolved_at"])
                self.assertEqual(resolutions, [])
            else:
                self.assertEqual(bug["status"], "Closed")
                self.assertEqual(len(resolutions), 1)
                self.assertEqual(resolutions[0]["related_bug_id"], bug_id)
                self.assertEqual(resolutions[0]["sprint_day"], resolved_day)
                self.assertEqual(resolutions[0]["timestamp"], bug["resolved_at"])
                self.assertGreater(bug["resolved_at"], bug["created_at"])
        self.assertTrue(self.bug_by_id["BUG-002"]["blocking"])

    def test_three_traceable_qa_rejections(self):
        rejections = [event for event in self.events if event["event_type"] == "returned_to_dev"]
        self.assertEqual(len(rejections), 3)
        self.assertEqual({event["work_item_id"] for event in rejections}, set(BUG_LINKS.values()))
        for event in rejections:
            self.assertEqual((event["from_state"], event["to_state"]), ("QA", "Returned to DEV"))
            bug = self.bug_by_id[event["related_bug_id"]]
            self.assertEqual(bug["work_item_id"], event["work_item_id"])
            self.assertIs(bug["blocks_story_closure"], True)
            self.assertGreater(event["timestamp"], bug["created_at"])
            self.assertEqual(event["timestamp"][:10], bug["created_at"][:10])

    def test_qa_outcome_evidence(self):
        # Fixture expectations only: no rate, denominator, or product metric is calculated.
        for item_id in {"US-101", "US-103", "US-106", "US-110", "US-111"}:
            self.assertEqual(len(self.events_for(item_id, "qa_passed")), 1)
            self.assertEqual(self.events_for(item_id, "bug_detected"), [])
            self.assertEqual(self.events_for(item_id, "returned_to_dev"), [])
        for item_id in {"US-102", "US-105"}:
            rejection = self.events_for(item_id, "returned_to_dev")[0]
            reentry = self.events_for(item_id, "entered_qa")[-1]
            passed = self.events_for(item_id, "qa_passed")
            self.assertEqual(len(passed), 1)
            self.assertGreater(reentry["timestamp"], rejection["timestamp"])
            self.assertGreater(passed[0]["timestamp"], reentry["timestamp"])
            self.assertEqual(reentry["related_bug_id"], rejection["related_bug_id"])
        self.assertEqual(self.events_for("US-104", "qa_passed"), [])
        for item_id in CLOSED_DAYS:
            self.assertLess(
                self.events_for(item_id, "qa_passed")[0]["timestamp"],
                self.events_for(item_id, "closed")[0]["timestamp"],
            )

    def test_task_hours_and_completion(self):
        self.assertEqual({task["work_item_id"] for task in self.tasks}, set(self.item_by_id))
        for task in self.tasks:
            with self.subTest(task=task["id"]):
                self.assertIn(task["type"], TASK_TYPES)
                for field in ("estimated_hours", "completed_hours", "remaining_hours"):
                    self.assertIsInstance(task[field], (int, float))
                    self.assertNotIsInstance(task[field], bool)
                    self.assertTrue(math.isfinite(task[field]))
                    self.assertGreaterEqual(task[field], 0)
                self.assertGreater(task["estimated_hours"], 0)
                if task["state"] == "Closed":
                    self.assertIsNotNone(task["completed_at"])
                    self.assertEqual(task["remaining_hours"], 0)
                    self.assertGreaterEqual(task["completed_at"], task["created_at"])
                else:
                    self.assertIsNone(task["completed_at"])
                    self.assertGreater(task["remaining_hours"], 0)
                if task["work_item_id"] in CLOSED_DAYS:
                    self.assertEqual(task["state"], "Closed")
                    self.assertLessEqual(
                        task["completed_at"], self.events_for(task["work_item_id"], "closed")[0]["timestamp"]
                    )

    def test_v01_source_and_effort_enums(self):
        for item in self.items:
            self.assertIn(item["source"], SOURCES, item["id"])
        for task in self.tasks:
            self.assertIn(task["effort_kind"], EFFORT_KINDS, task["id"])

    def test_source_is_independent_of_carry_over(self):
        for number in range(101, 111):
            item = self.item_by_id[f"US-{number}"]
            self.assertEqual(item["source"], "roadmap")
            self.assertTrue(item["original_baseline"])
            self.assertFalse(item["scope_added_after_baseline"])
        self.assertTrue(self.item_by_id["US-110"]["carry_over"])
        added = self.item_by_id["US-111"]
        self.assertEqual(added["source"], "client_incident")
        self.assertTrue(added["scope_added_after_baseline"])
        self.assertFalse(added["original_baseline"])
        self.assertFalse(added["carry_over"])

    def test_scope_added_effort_does_not_reclassify_baseline_work(self):
        for task in self.tasks:
            with self.subTest(task=task["id"]):
                item = self.item_by_id[task["work_item_id"]]
                if item["id"] == "US-111":
                    self.assertEqual(task["effort_kind"], "scope_added")
                    self.assertTrue(item["scope_added_after_baseline"])
                    self.assertFalse(item["original_baseline"])
                else:
                    self.assertTrue(item["original_baseline"])
                    self.assertIn(task["effort_kind"], {"planned", "rework"})
                    if task["related_bug_id"] is None:
                        self.assertEqual(task["effort_kind"], "planned")
                if task["type"] in {"Bug Fix", "QA Recertification"}:
                    self.assertEqual(task["effort_kind"], "rework")

    def test_rework_tasks_have_prior_linked_qa_rejection(self):
        for task in self.tasks:
            if task["effort_kind"] != "rework":
                continue
            with self.subTest(task=task["id"]):
                rejections = [
                    event for event in self.events_for(task["work_item_id"], "returned_to_dev")
                    if event["related_bug_id"] == task["related_bug_id"]
                    and event["from_state"] == "QA"
                    and event["to_state"] == "Returned to DEV"
                    and event["timestamp"] <= task["created_at"]
                ]
                self.assertEqual(len(rejections), 1)

    def test_separate_planned_rework_and_scope_added_tasks(self):
        for task in self.tasks:
            self.assertIn(task["effort_kind"], EFFORT_KINDS)
            if task["effort_kind"] == "rework":
                self.assertIn(task["related_bug_id"], BUG_LINKS)
                self.assertGreater(task["created_at"], self.bug_by_id[task["related_bug_id"]]["created_at"])
                self.assertIn(task["type"], {"Bug Fix", "QA Recertification", "Code Review / Integration"})
            else:
                self.assertIsNone(task["related_bug_id"])
                self.assertNotIn(task["type"], {"Bug Fix", "QA Recertification"})
                expected_date = self.calendar[6 if task["work_item_id"] == "US-111" else 1]
                self.assertEqual(task["created_at"][:10], expected_date)
        for bug_id, item_id in BUG_LINKS.items():
            fixes = [task for task in self.tasks if task["related_bug_id"] == bug_id and task["type"] == "Bug Fix"]
            self.assertEqual(len(fixes), 1)
            self.assertEqual(fixes[0]["work_item_id"], item_id)
            certifications = [task for task in self.tasks if task["work_item_id"] == item_id and task["type"] == "QA Certification"]
            self.assertEqual(len(certifications), 1)
            self.assertEqual(certifications[0]["effort_kind"], "planned")
            self.assertEqual(certifications[0]["completed_at"], self.bug_by_id[bug_id]["created_at"])
            if bug_id == "BUG-002":
                self.assertIsNone(fixes[0]["completed_at"])
            else:
                recertifications = [task for task in self.tasks if task["related_bug_id"] == bug_id and task["type"] == "QA Recertification"]
                self.assertEqual(len(recertifications), 1)
                self.assertEqual(recertifications[0]["completed_at"], self.events_for(item_id, "qa_passed")[0]["timestamp"])


if __name__ == "__main__":
    unittest.main()
