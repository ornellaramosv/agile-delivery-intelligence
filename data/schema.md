# Fictional sprint data schema

This document describes the Sprint 08 JSON fixture, not a production API or database schema. Identifiers are strings, dates use `YYYY-MM-DD`, and timestamps use ISO 8601 UTC (`Z`). Array files contain records with unique `id` values. Snapshot fields describe the end of Day 10 unless stated otherwise.

## Sprint (`sprint.json`, one object)

| Field | Meaning |
| --- | --- |
| id, name | Sprint identifier and display name |
| project, backlog | Fictional project and backlog names |
| start_date, end_date | Inclusive sprint dates |
| timezone | `UTC` for this fixture |
| baseline_at | Time the original baseline is recorded |
| snapshot_at | Time represented by final record snapshots |
| original_baseline_work_item_ids | Fixed opening membership; scope additions never alter it |
| working_days | Ordered objects containing `sprint_day` (1–10) and `date` |

The scenario folder associates the other files with this sprint; no redundant `sprint_id` fields or cross-sprint membership model are introduced.

## Work Item (`work-items.json`)

| Field | Meaning |
| --- | --- |
| id, title | Story identifier and fictional description |
| type | `User Story` |
| backlog | `Core Services` |
| state | Final normalized workflow state |
| original_baseline | Boolean; membership in the fixed original sprint baseline |
| scope_added_after_baseline | Boolean; formally added after baseline recording |
| carry_over | Boolean; committed in the previous sprint and carried into this one |
| source | Origin of work: `roadmap` or `client_incident`; carry-over is not a source |

US-101 through US-110 use `roadmap`. Only US-110 is carry-over; its source remains `roadmap`. Only US-111 is added scope and uses `client_incident`. Opening/entry states and closure timestamps come from events rather than duplicate Work Item fields.

## Task (`tasks.json`)

| Field | Meaning |
| --- | --- |
| id, title | Task identifier and description |
| work_item_id | Reference to the parent Work Item |
| type | Development, Code Review / Integration, QA Certification, Bug Fix, or QA Recertification |
| effort_kind | Reason effort is consumed: `planned`, `rework`, or `scope_added` |
| estimated_hours | Original estimate at task creation; not replaced by actual effort or later rework |
| completed_hours | Cumulative effort spent by the snapshot, including on unfinished tasks |
| remaining_hours | Remaining estimate at the snapshot; zero for a completed task |
| state | Final normalized workflow state |
| created_at | Time the task was created, not necessarily when execution started |
| completed_at | Time task execution finished, or `null` if unfinished |
| related_bug_id | Originating defect for rework tasks, otherwise `null` |

Hours are nonnegative numbers, and estimates are positive in this fixture. No equality between original estimate and actual-plus-remaining hours is assumed. Rework gets separate tasks, leaving planned estimates intact. Normal baseline effort uses `planned`. Defect-driven Bug Fix, QA Recertification, and associated review/integration tasks use `rework`. All tasks for US-111 use `scope_added`. These categories do not describe employee productivity. Closed QA tasks can represent failed test execution; story acceptance is recorded separately in events. Tasks do not include assignees or employee rankings.

## Bug (`bugs.json`)

| Field | Meaning |
| --- | --- |
| id, title | Bug identifier and description |
| work_item_id | Reference to the affected Work Item |
| created_at | QA detection time |
| resolved_at | Verified resolution/bug closure time, or `null` while unresolved |
| status | `Open` or `Closed` defect lifecycle status |
| blocking | Boolean; retained legacy “blocking defect” marker, true only for BUG-002; not the story-closure criterion |
| blocks_story_closure | Required boolean; whether the unresolved Bug prevents the related User Story from reaching Closed |

Bug lifecycle status is separate from normalized Work Item/task workflow state. Neither boolean automatically introduces a Blocked state transition.

`blocks_story_closure` is a required boolean. When true, the related User Story cannot reach final completion at `Closed` while the Bug is unresolved; the story may return to Development, and the open Bug represents additional delivery work that future Burndown logic may count as one additional unit. When false, the Bug does not prevent story closure and must not automatically increase Current Remaining Work. This permits future Consideration/deferred-work cases without implementing them here.

The existing `blocking` field is retained unchanged as the original fixture's “blocking defect” marker (true only for BUG-002). It is a different concept from `blocks_story_closure`; it is not the criterion for story acceptance or Current Remaining Work. No new criticality or release-gating meaning is assigned to that legacy field. All three Sprint 08 Bugs have `blocks_story_closure = true` because all three caused QA rejection and return to DEV.


## Delivery Event (`delivery-events.json`)

| Field | Meaning |
| --- | --- |
| id | Unique event identifier |
| work_item_id | Reference to the affected Work Item |
| event_type | One of the event types below |
| from_state, to_state | Normalized story states before and after the event |
| sprint_day | Working-day number, 1–10 |
| timestamp | Event time, consistent with the sprint-day calendar |
| related_bug_id | Related bug for defect/rework context, otherwise `null` |
| description | Fictional causal context or scope decision |

Event types: `sprint_started`, `scope_added`, `code_integration_started`, `ready_for_qa`, `entered_qa`, `bug_detected`, `returned_to_dev`, `qa_passed`, `bug_resolved`, `closed`.

Events are ordered by timestamp. `from_state` is `null` only for the opening snapshot or new scope entry; this is absence of prior in-sprint membership, not an extra workflow state. Context events (`bug_detected`, `qa_passed`, `bug_resolved`) retain the current state. Each story's event chain ends at its final Work Item state. Events starting a rework phase reference the corresponding bug.

## Normalized workflow states

- Development
- Code Integration
- Ready for QA
- QA
- Returned to DEV
- Blocked
- Closed

These are the only Work Item/task state values. Not every state must occur in this scenario. Validation checks this fixture's consistency; it does not establish general product transition rules or implement metrics.

## v0.1 delivery-work semantics

Burndown uses **remaining delivery work items**, not hours. Hours describe Task effort and belong to future Capacity Health; they are not a v0.1 Burndown input.

The original baseline is an immutable set of 10 User Stories. **Original Baseline** and **Current Remaining Work** are separate concepts: an open Bug with `blocks_story_closure = true` represents additional delivery work, and a formally scope-added User Story represents additional delivery work while open. Their arrival may increase Current Remaining Work without changing original baseline membership. A User Story remains delivery work until Closed; a handoff to QA does not complete it.

An open Bug with `blocks_story_closure = true` represents additional delivery work and may increase Current Remaining Work. All three fixture Bugs meet that condition while open; US-111 is the formally added User Story. The legacy `blocking` marker is independent. The [Burndown engine](../docs/burndown-intelligence.md) implements these semantics; the fixture stores records and events, not calculated series.

## Dataset freeze

**Dataset version: v1 — frozen for Sprint Intelligence implementation**

Frozen story IDs, bug IDs, dates, workflow events, task effort, initial states, final states, baseline membership, and scope-added membership must not change during Sprint Intelligence implementation unless a Product Owner-approved defect is discovered. The validation suite pins the semantic contents of all five JSON files with SHA-256 digests (formatting and object-key order are ignored). Do not refresh these digests to accommodate implementation changes; an approved dataset defect is required.

## Capacity Health evidence (v0.2)

The six additional Sprint 08 files and two `capacity-history` files are **fictional additive evidence**, not part of the frozen v1 file set. Existing v1 records and digests are unchanged. See [Capacity Health](../docs/capacity-health.md) for calculations and semantics.

| File | Shape and required evidence |
| --- | --- |
| `sprint-08/capacity-plan.json` | Sprint ID, `disciplines` (DEV/QA), `daily_schedule` with sprint day/date and gross hours per discipline, `reserves` with support/regression hours. Planning allocations, not calculated capacity. |
| `sprint-08/task-capacity-map.json` | One `{task_id, discipline}` per frozen Task. No duplicated estimates, completed/remaining totals or effort classifications. |
| `sprint-08/capacity-ledger.json` | `time_entries` with unique ID, UTC timestamp, positive hours and **either** Task ID **or** category/reference ID/discipline. Non-task categories: support, release_regression, technical_enablement. Task categories come from frozen effort_kind. `task_remaining_observations`: unique ID, timestamp, Task ID, non-negative remaining hours. |
| `sprint-08/dependencies.json` | ID, type, owning technical area, affected Work Item IDs, opened/resolved timestamps (nullable resolution), description, dated remaining-hour observations per discipline. Technical time entries reference dependency IDs. |
| `sprint-08/scope-decisions.json` | ID, Work Item ID, support case ID, delivery event ID, timestamp, recorded decision. Entry time must match the frozen scope event. |
| `sprint-08/release-regression.json` | Release ID, previous release ID, explicit story scope, included customer case IDs, dated regression start/completion event IDs, observed remaining hours. Current stories reference frozen events; older stories include origin sprint, closure timestamp and certification evidence ID. Null represents no active release. |
| `capacity-history/support-cases.json` | `historical_sprints`: sprint ID/start date, positive recency weight, evidence_complete flag, individual cases with ID, case_class and actual effort by area. `current_cases`: ID, case_class, received timestamp, planning remaining hours, nullable linked Work Item ID, nullable customer closure, engineering lifecycle events and remaining observations. Converted cases also reference the frozen scope event. |
| `capacity-history/regression-history.json` | Release ID, positive scope count, non-negative actual QA hours, positive recency weight. Weights sum to one. Missing/invalid scope evidence cannot produce a forecast. |

`case_class` is `standard` or `critical`. Engineering lifecycle events in this fixture are received, qa_validation, technical_investigation, not_reproducible, entered_sprint, prepared_for_future_release, engineering_closed. They are support lifecycle evidence, **not new User Story workflow states**. Customer closure is independent. Critical events may retain bypass/displacement/urgent-package context. External-area hours remain evidence, not automatically DEV/QA consumption.

All effort is non-negative and team-level. Ledger Task entries reconcile to final frozen completed hours and occur between creation and completion/final snapshot; intermediate remaining observations preserve re-estimation without overwriting original estimates. Support entries for a converted case precede formal sprint entry; post-entry work is represented once by its Tasks. Regression effort is QA-only and occurs inside its recorded execution window after release readiness. Dependency effort is separate from elapsed duration. No forecasts, capacity snapshots, gaps, pressure, health conclusions, or employee identifiers are stored.

Historical zero-case observations are explicit complete periods, distinct from missing history. They inform frequency but cannot alone establish hours per case. Forecast statuses are calculated, insufficient_history, or not_applicable. These and primary answers are **engine outputs**, not stored fixture values. Unknown required forecasts propagate null; known lower bounds can prove a no, and zero delivery demand yields yes. See the approved [missing-evidence rules](../docs/capacity-health.md#remaining-capacity-and-the-primary-answer).
