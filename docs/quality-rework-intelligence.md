# Quality & Rework Intelligence

First-pass QA measures whether eligible User Stories pass QA without returning to Development for defect correction. It is a delivery-flow quality signal at sprint/team/backlog level, **not an individual developer-performance metric**. The response contains no people, rankings, health labels, or threshold interpretation.

## v0.1 population and first attempt

Eligible stories have `source = roadmap` and reached QA during the sprint. Roadmap carry-over is included; carry-over is not an exclusion. Client-incident work is excluded from this metric under the explicit v0.1 Product Owner decision, including Sprint 08's scope-added incident. This is not a universal Agile rule. Roadmap scope addition is not itself an exclusion.

A Day 1 `sprint_started` entry into QA counts as the first observed attempt. The frozen audit establishes that these opening QA stories are on their first attempt. Other stories begin their observed attempt when workflow events first enter QA. Opening evidence and transition evidence are retained as event IDs.

The first recorded attempt outcome is fixed:

- `qa_passed` while in QA establishes `passed` if no earlier QA → Returned to DEV rejection occurred.
- QA → Returned to DEV establishes `failed`, including an unresolved defect. Later certification or Closed delivery never overwrites that failure.
- Roadmap stories that never entered QA are `not_reached_qa` and excluded from the denominator.
- Client-incident stories are `excluded`, with an explicit reason. Their rework, if any, remains visible in rework analysis.

Closed state alone is not QA-certification evidence. For a future eligible story with no recorded certification or rejection, the outcome is null with a reason, not an invented success/failure or a new classification. It remains in the requested reached-QA denominator. Successes and failures therefore need not exhaust the denominator for an incomplete history. Sprint 08 has no such unknown outcomes.

`first_pass_qa_rate` is the unrounded ratio `successes / eligible_qa_stories`, on a 0–1 scale for frontend formatting. It is null when no stories are eligible.

QA performs certification/validation; a User Story reaches final completed state only at `Closed`. A QA → Returned to DEV transition records required rework before final closure. These fixture conventions do not assign universal product-acceptance ownership to QA. Existing API fields named `acceptance_event_id` and `acceptance_event_ids` refer to `qa_passed` certification evidence, not the later `closed` event; their names and calculations remain unchanged.

## Rework cycles and evidence

Each actual QA → Returned to DEV transition creates one cycle. Bugs and Tasks alone never create cycles. A story can have zero to many cycles; cycle IDs use the originating return-event ID and cycle numbers are sequential per story.

For each cycle the engine preserves:

- story ID, day, timestamp, and return event;
- QA rejection evidence (the return transition itself);
- the preceding linked QA Bug-detection event where available;
- linked Bug ID, original Bug-record status, and event-derived resolution status/event;
- subsequent QA-entry events for recertification and certification-result evidence.

Missing Bug links remain null rather than being inferred from story ownership. Unique linked Bugs are counted once even if involved in more than one cycle. Event-derived resolution is distinct from the Bug record's final status.

The implementation convention for cycle completion is explicit QA certification following re-entry to QA. Returning to QA, closing a Bug, or a final Closed snapshot alone does not complete a cycle. Cycles awaiting that certification remain `active` at sprint end. If repeated rejections happen before certification passes, each remains a separately evidenced cycle; the later certification pass completes all still-active cycles that have recertification evidence. `resolved_rework_cycles` counts cycles with status `completed`, not resolved Bugs. This convention does not change any frozen record or existing engine behavior.

## Rework effort

Aggregate active-scope Tasks explicitly labeled `effort_kind = rework`: task count, estimated, completed, and remaining hours, plus Task IDs. Provide both sprint totals and per-story totals. Task type and Bug count do not substitute for effort classification. Tasks without rejection evidence can still be reported as labeled effort, but cannot invent cycles.

Completed plus remaining hours may exceed the estimate. Values are summed as recorded without normalization. This is effort associated with rework, not Capacity Health. No effort allocation across multiple cycles is invented.

## Domain and endpoint

`calculate_quality_rework(sprint=..., work_items=..., bugs=..., tasks=..., events=...)` is a pure Python function under `app/domain/quality_rework`. It reuses the approved Delivery Flow function unchanged for validated active scope and event-derived final states. It orders event evidence by timestamp/ID and output stories by ID. It does not read Work Item final snapshot states as calculation inputs or mutate records.

The application service loads the five frozen files. `GET /demo/sprint-08/quality-rework` delegates to it and returns:

- `sprint`: sprint metadata;
- `quality_summary`: population, first-pass outcome counts/rate, rework story/cycle/Bug counts, and effort totals;
- `stories`: per-story eligibility/outcome/reason, final state, cycle count, linked Bugs, evidence, and effort;
- `rework_cycles`: structured transition, defect, recertification, certification-result, and status evidence;
- `rework_effort`: sprint task totals and contributing Task IDs.

The domain response includes no chart configuration or styling. A separate [Quality & Rework UI](quality-rework-ui.md) now presents these results. No persistence, individual rankings, or additional intelligence capability is included.

## Frozen Sprint 08 expectations

| Stories | First-pass outcome |
| --- | --- |
| US-101, US-103, US-106, US-110 | passed |
| US-102, US-104, US-105 | failed |
| US-107, US-108, US-109 | not_reached_qa |
| US-111 | excluded (client incident) |

Eligible population: 7. Successes: 4. Failures: 3. Ratio: 4/7 (approximately 57.1%). Three stories have three traceable cycles, linked to three Bugs. Two cycles are completed; US-104 / BUG-002 remains active and unresolved.

| Story | Rework tasks | Estimated hours | Completed hours | Remaining hours |
| --- | ---: | ---: | ---: | ---: |
| US-102 | 3 | 13 | 15 | 0 |
| US-104 | 1 | 16 | 12 | 8 |
| US-105 | 3 | 16 | 18 | 0 |
| Total | 7 | 45 | 45 | 8 |

These are fixture assertions, not constants in business logic. Tests also vary records in memory to exercise multiple cycles, missing evidence, empty populations, independent Bug/Task existence, deterministic execution, and API/domain parity. Frozen data and earlier intelligence implementations remain unchanged.
