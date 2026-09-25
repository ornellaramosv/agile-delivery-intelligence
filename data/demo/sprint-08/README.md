# Atlas — Core Services — Sprint 08

This fictional two-week sprint represents successful QA, QA rejection and rework, unfinished work, carry-over, and a formally accepted client incident. All project names, IDs, dates, hours, and records are fictional; no real employer, client, employee, or proprietary project records are used.

**This dataset is designed to test delivery-intelligence behavior, not employee performance.**

It provides inspectable inputs for the implemented Burndown, Delivery Flow, and Quality & Rework engines and read-only demo APIs. The dataset has no editing API or persistence.

## Files

| File | Contents |
| --- | --- |
| `sprint.json` | Project/backlog, calendar, opening baseline membership, snapshot time |
| `work-items.json` | 11 User Stories with scope flags and end-of-sprint states |
| `tasks.json` | 25 tasks with original estimates and final effort snapshots |
| `bugs.json` | 3 defects with creation and resolution timestamps |
| `delivery-events.json` | 50 chronological workflow and context events |
| `AUDIT.md` | Human-readable story, bug, task-effort, and daily event review |

## Sprint calendar

All timestamps use UTC (`Z`). The sprint opens at 09:00 on Day 1; the final snapshot is at 18:00 on Day 10. Weekends are outside the working-day calendar.

| Sprint day | Date | Weekday |
| --- | --- | --- |
| 1 | 2030-04-08 | Monday |
| 2 | 2030-04-09 | Tuesday |
| 3 | 2030-04-10 | Wednesday |
| 4 | 2030-04-11 | Thursday |
| 5 | 2030-04-12 | Friday |
| 6 | 2030-04-15 | Monday |
| 7 | 2030-04-16 | Tuesday |
| 8 | 2030-04-17 | Wednesday |
| 9 | 2030-04-18 | Thursday |
| 10 | 2030-04-19 | Friday |

## Baseline and additional scope

The original baseline is exactly **US-101 through US-110**. `original_baseline_work_item_ids` records that fixed membership at `baseline_at`; the Work Item flags must agree with it.

US-111 is a client incident validated and formally accepted at 09:30 on Day 6. Its `scope_added` event records that decision. It has `source: "client_incident"`, `original_baseline: false`, and `scope_added_after_baseline: true`. It never enters the baseline list. Its tasks are created after acceptance.

US-101 through US-110 use `source: "roadmap"`. Source describes work origin, not carry-over. Only US-110 is carry-over, and its source remains `roadmap`. It begins in Ready for QA and enters its first QA attempt on Day 2. The previous sprint's records are outside this fixture.

## Expected story outcomes

These are scenario acceptance expectations, not stored metric outputs.

| Story | Opening state / entry | QA and rework context | Final state |
| --- | --- | --- | --- |
| US-101 | QA, Day 1 | First attempt passes | Closed, Day 2 |
| US-102 | QA, Day 1 | BUG-001 on Day 3; one return to DEV; recertified Day 7 | Closed, Day 7 |
| US-103 | QA, Day 1 | Slower first attempt passes | Closed, Day 8 |
| US-104 | QA, Day 1 | Blocking BUG-002 on Day 4; one return to DEV; fix unfinished | Returned to DEV |
| US-105 | Development, Day 1 | First QA entry Day 6; BUG-003 on Day 7; one return to DEV | Closed, Day 10 |
| US-106 | Development, Day 1 | First attempt passes | Closed, Day 10 |
| US-107 | Development, Day 1 | Reaches Code Integration on Day 10; no QA attempt | Code Integration |
| US-108 | Development, Day 1 | Development unfinished; no QA attempt | Development |
| US-109 | Development, Day 1 | Development unfinished; no QA attempt | Development |
| US-110 | Ready for QA, Day 1 | Carry-over; first attempt passes | Closed, Day 6 |
| US-111 | Development, Day 6 | Added client incident; QA passes | Closed, Day 10 |

Closed baseline stories are US-101, US-102, US-103, US-105, US-106, and US-110. The four remaining baseline stories stay open. US-111 closes separately as added scope.

## Defects and effort

- **BUG-001 / US-102:** detected on Day 3; fix, integration, and QA recertification are separate rework tasks. QA verifies resolution and the bug closes on Day 7.
- **BUG-002 / US-104:** blocking defect detected on Day 4. Its Bug Fix task remains unfinished, the bug remains Open, and the story remains Returned to DEV at the final snapshot. No Blocked transition is invented.
- **BUG-003 / US-105:** detected on Day 7; separate fix, integration, and recertification tasks lead to bug closure on Day 10.

Each rejection has a `bug_detected` event followed by a linked `QA → Returned to DEV` event. These are the three scenario rework cycles; a cycle here means a QA rejection requiring development rework, even when unresolved at sprint end.

Task `effort_kind` describes why effort is consumed. The only v0.1 values are `planned`, `rework`, and `scope_added`. Normal baseline tasks use `planned`; defect-driven Bug Fix, QA Recertification, and associated integration tasks use `rework`. All three tasks for US-111 use `scope_added`. Rework tasks reference their originating bug and a preceding QA rejection. Original planned task estimates remain separate and unchanged. These labels do not measure employee productivity.

Task hours are final cumulative snapshots, not daily timesheets. `estimated_hours` is the estimate at task creation; `completed_hours` is effort already spent; `remaining_hours` is the latest remaining estimate. Actual plus remaining effort need not equal the original estimate. A completed QA task means test execution finished, even when it found a defect; it does **not** mean the User Story passed QA or closed. QA certification is represented by `qa_passed`; final User Story completion is represented by `closed`.

For stories already in QA, tasks cover certification and subsequent rework within this sprint; prior development/integration effort is not invented. Task categories and workflow states are documented in [the data schema](../../schema.md).

## History and QA interpretation

`sprint_started` establishes the opening state. Stories starting in QA are explicitly on their first attempt in this scenario; that snapshot does not manufacture a new QA entry. `scope_added` establishes US-111's initial state on Day 6. These are the only events with `from_state: null`.

`bug_detected`, `bug_resolved`, and `qa_passed` preserve the story state (`QA → QA`) while recording context. `bug_resolved` means the defect has been verified and closed in this fixture; `resolved_at` is that timestamp. State-changing events form a continuous chain ending at each Work Item's final `state`.

For first-pass QA, successful normal backlog stories are US-101, US-103, US-106, and US-110; failures are US-102, US-104, and US-105. The expected result is **4 / 7 ≈ 57.1%**. US-111 must be excluded because it is added client-incident scope, and US-107–109 never reach QA. This expectation is now calculated by the Quality & Rework engine; no QA rate is stored in the frozen dataset.

## Validation

From the repository root, using Python's standard library:

```sh
python3 -m unittest discover -s data/tests -v
```

Validation checks IDs and references, baseline/scope/carry-over flags, the calendar and timestamps, normalized states, event continuity, closure days, bug links and lifecycles, the three QA rejections, QA outcome evidence, task effort/completion consistency, allowed v0.1 enums, source/carry-over independence, and protection against baseline effort being reclassified as added scope, explicit boolean story-closure flags, and frozen v1 JSON content. Tests assert fixture expectations; they are not an analytics implementation.

## Dataset freeze

**Dataset version: v1 — frozen for Sprint Intelligence implementation**

Frozen story IDs, bug IDs, dates, workflow events, task effort, initial states, final states, baseline membership, and scope-added membership must not change during Sprint Intelligence implementation unless a Product Owner-approved defect is discovered. The validation suite pins the semantic contents of all five JSON files with SHA-256 digests (formatting and object-key order are ignored). Do not refresh these digests to accommodate implementation changes; an approved dataset defect is required.

## Confirmed v0.1 semantics

Burndown uses **remaining delivery work items**, not hours. Hours belong to Task effort and future Capacity Health. Original Baseline remains the immutable 10 User Stories and is separate from Current Remaining Work.

An open Bug with `blocks_story_closure = true` represents additional delivery work and may increase Current Remaining Work. A formally scope-added User Story represents additional delivery work while open. Creating the former or accepting the latter can increase Current Remaining Work without changing the original baseline. All three Bugs block story closure while unresolved, independently of the legacy `blocking` marker; US-111 provides the added-scope case. No Burndown calculation is implemented here.

`blocks_story_closure` is a required boolean. When true, the related User Story cannot reach final completion at `Closed` while the Bug is unresolved; the story may return to Development, and the open Bug represents additional delivery work that future Burndown logic may count as one additional unit. When false, the Bug does not prevent story closure and must not automatically increase Current Remaining Work. This permits future Consideration/deferred-work cases without implementing them here.

The existing `blocking` field is retained unchanged as the original fixture's “blocking defect” marker (true only for BUG-002). It is a different concept from `blocks_story_closure`; it is not the criterion for story acceptance or Current Remaining Work. No new criticality or release-gating meaning is assigned to that legacy field. All three Sprint 08 Bugs have `blocks_story_closure = true` because all three caused QA rejection and return to DEV.


The `source` and `effort_kind` meanings and allowed values are confirmed for v0.1. The fixture remains an end-of-sprint snapshot plus an ordered event log, not a production ingestion schema. A rework cycle in this scenario is a QA rejection requiring development rework, including the unresolved return for US-104. A Closed QA task records finished test execution, not story acceptance.

See [AUDIT.md](AUDIT.md) for Product review without reading JSON. Its Task-hour totals are a static audit aid only, not Capacity Health or employee performance analysis. No Product Owner decision remains open for these semantics.
