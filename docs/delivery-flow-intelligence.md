# Delivery Flow Intelligence

Burndown answers: **How much delivery work remains?**
Delivery Flow answers: **Where is the User Story work currently located?**

These views complement each other. Burndown can include open story-closure-blocking Bugs as additional delivery work. Flow counts only active-scope User Stories, including Closed stories, once each. It does not count Bugs or Task hours. Workflow-state reporting itself is not unique to ADI; ADI's value will come from connecting flow position with other causal delivery signals.

## Replay and scope

The pure `calculate_delivery_flow(sprint=..., work_items=..., events=...)` function in `apps/api/app/domain/delivery_flow` reconstructs end-of-day positions from events. It does not read files, call FastAPI, inspect final Work Item states, or infer state from Bug status.

- Baseline `sprint_started` events establish Day 1 opening positions. There is no second initial-state source.
- The formal `scope_added` event activates additional scope. US-111 is absent on Days 1–5 and present from Day 6. Original baseline membership remains unchanged.
- Events are replayed by timestamp, with event ID breaking ties, within each working day. Timestamps must match the working date in the sprint timezone.
- Every transition must start at the story's current state. Invalid references, unknown states, missing baseline openings, duplicate scope entries, and discontinuous histories are rejected.
- Same-state events and records with both state fields null are context only. They never move a story. A partial transition with no destination is rejected rather than guessed.
- QA rejection moves a story to `Returned to DEV`, where it remains until another transition. Bug resolution alone cannot move it.

The seven states are Development, Code Integration, Ready for QA, QA, Returned to DEV, Blocked, and Closed. All are returned, including zero counts. Each snapshot includes `story_states` keyed by story ID to audit the counts; `open_stories + closed_stories == total_active_scope`. Closed stories stay in the active scope population.

## Demo endpoint and response

`GET /demo/sprint-08/delivery-flow` loads the three frozen sprint, Work Item, and Delivery Event files via a separate application service. The route delegates to the domain engine without calculations.

Response fields:

- `sprint`: ID, name, project, backlog, start/end dates, timezone.
- `workflow_states`: the ordered normalized state list.
- `daily_snapshots`: working day/date, `states` counts, `story_states`, `open_stories`, `closed_stories`, and `total_active_scope`.
- `daily_movements`: working day/date, `movements`, and `scope_entries`.

Each movement includes event ID, story ID, timestamp, from-state, and to-state. Only actual changes between workflow states appear in `movements`. Initial and scope-added entries have a null from-state and appear separately in `scope_entries`; null is not a workflow state. This preserves entry evidence without presenting population additions as workflow transitions. Both daily lists include all ten days even when empty. No chart configuration is returned.

## Frozen Sprint 08 results

| Day | Development | Code Integration | Ready for QA | QA | Returned to DEV | Blocked | Closed | Active scope |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 5 | 0 | 1 | 4 | 0 | 0 | 0 | 10 |
| 2 | 5 | 0 | 0 | 4 | 0 | 0 | 1 | 10 |
| 3 | 5 | 0 | 0 | 3 | 1 | 0 | 1 | 10 |
| 4 | 4 | 1 | 0 | 2 | 2 | 0 | 1 | 10 |
| 5 | 4 | 0 | 1 | 2 | 2 | 0 | 1 | 10 |
| 6 | 5 | 0 | 1 | 2 | 1 | 0 | 2 | 11 |
| 7 | 4 | 1 | 0 | 1 | 2 | 0 | 3 | 11 |
| 8 | 3 | 1 | 1 | 0 | 2 | 0 | 4 | 11 |
| 9 | 3 | 0 | 1 | 2 | 1 | 0 | 4 | 11 |
| 10 | 2 | 1 | 0 | 0 | 1 | 0 | 7 | 11 |

Day 10 open stories are US-104 (Returned to DEV), US-107 (Code Integration), and US-108/109 (Development). The other seven stories are Closed. These expectations are assertions against the fixture, not constants in the engine.

US-102 illustrates why movements accompany snapshots: QA on Day 1 → Returned to DEV on Day 3 (EVT-015) → Code Integration on Day 6 (EVT-023) → Ready for QA later Day 6 (EVT-025) → QA on Day 7 (EVT-026) → Closed later Day 7 (EVT-032). Its intermediate Code Integration state is visible in movements even though it is not its end-of-day state.

The current fixture's `bug_detected`, `qa_passed`, and `bug_resolved` records have equal from/to states and are intentionally excluded from movements. Classification depends on the actual state fields, not the event label.

## Validation and boundaries

Domain tests assert daily distributions, exactly-once membership, scope timing, complete rework paths, context exclusion, final positions, deterministic ordering, non-mutation, and API/domain parity. In-memory event variations demonstrate that states and membership are reconstructed rather than hardcoded. Data tests retain the existing frozen-fixture digest checks.

The separate [Delivery Flow UI](delivery-flow-ui.md) now presents this engine’s results. No cumulative-flow diagram, bottleneck scoring, flow-risk thresholds, QA or rework metrics, Capacity Health, or other capability is implemented by this engine. There is no pending Product Owner decision for this backend slice.
