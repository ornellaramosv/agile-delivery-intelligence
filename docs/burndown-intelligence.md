# Burndown Intelligence Engine

## Why this is not a traditional Burndown

A traditional Burndown answers “How much work remains?” ADI Burndown Intelligence additionally answers “What caused remaining work to change?” The engine retains the events behind increases and reductions, including opposing causes on a net-flat day. This describes ADI's behavior, not a claim that other tools cannot provide similar behavior through customization.

## Calculation boundary

The engine replays the frozen Sprint 08 v1 delivery history. It does not change the fixture, use Task hours, or read final Work Item states to infer earlier days. The [Sprint Health UI](sprint-health-ui.md) now presents this result without duplicating calculations. No database or unrelated Sprint Intelligence calculation is included.

Original Baseline is the fixed set of 10 User Stories. Current Remaining Work at the end of each working day consists of:

- Baseline stories that have not reached Closed.
- Formally scope-added stories that have entered the sprint and remain open.
- Created, unresolved Bugs with `blocks_story_closure = true`.

Each contributes one delivery-work unit. US-111 never changes baseline membership. A QA → Returned to DEV transition does not add a second story unit. The linked open Bug accounts for additional work. The legacy `blocking` flag and Task hours have no role in this calculation.

## Replay and traceability

Events are sorted by timezone-aware timestamp and then event ID for deterministic ties. The v1 calendar and timestamps are UTC. Each snapshot applies all events on its working day, including same-day creation and resolution. Missing working-day events leave the previous state in place.

Story entries, transitions, and closures come from delivery events. Bug creation/resolution events must match the timestamps in Bug records. Final Bug status is not replayed backward. Malformed histories, inconsistent scope flags, duplicate IDs, invalid references, and missing Bug lifecycle evidence raise `ValueError` rather than produce partial results. This is a domain engine for the current event contract, not a general-purpose ingestion API: it requires Day 1 opening snapshots and Bug lifecycles within the supplied sprint. Reopening a Closed story is outside this v0.1 contract and is rejected.

Every daily explanation retains ordered structured causes with `type`, `id`, `work_item_id`, `effect`, `event_id`, and `timestamp`:

| Cause type | Effect |
| --- | --- |
| `story_closed` | −1 |
| `scope_added` | +1 |
| `closure_blocking_bug_created` | +1 |
| `closure_blocking_bug_resolved` | −1 |

For Day 2 onward, delta is the difference from the previous snapshot. The sum of causal effects must equal delta. Day 1 establishes the first observation, so movement and delta are `null`; it does not assume an undocumented Day 0.

`active_rework_bugs` is a sorted list of unresolved Bug IDs with a prior linked QA → Returned to DEV event. It provides context, not additional work units. `composition` lists the IDs contributing to each of the three remaining-work categories. Counts in the snapshots and IDs in the composition allow consumers to inspect the result without interpreting Task effort.

## Insights and configuration

`BurndownConfig(flatline_threshold_days=2)` supplies the default. Callers may supply another positive integer directly to the engine or demo service. The HTTP demo uses the default configuration and reports it in its response.

Every positive daily delta produces an `upward_movement` insight with previous/current remaining work, delta, and all daily causes, including any opposing closures.

**Product Owner-confirmed v0.1 rule:** `delta < 0` is `down`, `delta == 0` is `flat`, and `delta > 0` is `up`. Flatline detection operates only on consecutive Flat days. Upward days are classified separately as Upward Movement and break a flatline; “without net reduction” must not be interpreted as including them. No Product Owner question remains open for this rule.

A possible future “No Reduction Streak” could include both flat and upward days. It is distinct from Flatline and is not implemented or included in v0.1 scope.

Day 1 is not a comparison day. A threshold of two means two successive zero-delta days, not two observations with only one comparison. The engine emits one maximal flat run, when the run ends or the sprint horizon is reached, rather than overlapping alerts. Context retains daily causes and event IDs, including workflow-only events with no work-unit effect. No UI notification is sent.

## Frozen Sprint 08 result

Original Baseline is **10 on every day**.

| Day | Date | Open baseline stories | Open added stories | Open closure-blocking Bugs | Current remaining | Delta |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2030-04-08 | 10 | 0 | 0 | 10 | — |
| 2 | 2030-04-09 | 9 | 0 | 0 | 9 | −1 |
| 3 | 2030-04-10 | 9 | 0 | 1 | 10 | +1 |
| 4 | 2030-04-11 | 9 | 0 | 2 | 11 | +1 |
| 5 | 2030-04-12 | 9 | 0 | 2 | 11 | 0 |
| 6 | 2030-04-15 | 8 | 1 | 2 | 11 | 0 |
| 7 | 2030-04-16 | 7 | 1 | 2 | 10 | −1 |
| 8 | 2030-04-17 | 6 | 1 | 2 | 9 | −1 |
| 9 | 2030-04-18 | 6 | 1 | 2 | 9 | 0 |
| 10 | 2030-04-19 | 4 | 0 | 1 | 5 | −4 |

Upward movements: Day 3, 9 → 10 from BUG-001 creation; Day 4, 10 → 11 from BUG-002 creation. Default flatline: Days 5–6, two zero-delta days at 11 remaining units. Day 9 is a single flat day and does not reach the default threshold.

Day 6 preserves both opposing causes:

```json
{
  "day": 6,
  "movement": "flat",
  "delta": 0,
  "causes": [
    {"type": "scope_added", "id": "US-111", "work_item_id": "US-111", "effect": 1, "event_id": "EVT-021", "timestamp": "2030-04-15T09:30:00Z"},
    {"type": "story_closed", "id": "US-110", "work_item_id": "US-110", "effect": -1, "event_id": "EVT-024", "timestamp": "2030-04-15T12:00:00Z"}
  ]
}
```

Day 7 has BUG-003 creation (+1), BUG-001 resolution (−1), and US-102 closure (−1), yielding a net reduction of one. Day 10 contains four open baseline stories (US-104, US-107, US-108, US-109) plus BUG-002, for five remaining units. No scope-added story remains open.

The earlier illustrative 9 → 10 movement on Day 3 agrees with the fixture. The earlier legacy `blocking` interpretation is superseded: BUG-001 and BUG-003 also contribute while unresolved because `blocks_story_closure` is true. The fixture was not adjusted to match a conversational total.

## Calling the engine and API

From `apps/api` with the virtual environment active:

```python
from app.domain.burndown import BurndownConfig
from app.services.demo_burndown import sprint_08_burndown

result = sprint_08_burndown(BurndownConfig(flatline_threshold_days=2))
```

The pure `calculate_burndown(sprint=..., work_items=..., bugs=..., events=..., config=...)` function accepts decoded JSON records and does no filesystem or network I/O. The service loads four files using paths relative to its module, not the shell working directory. Tasks are not loaded. Deployment of this demo endpoint must include the repository's data directory.

Run `python -m uvicorn app.main:app --reload` and request `GET /demo/sprint-08/burndown`. The response contains `sprint`, `configuration`, `daily_snapshots`, and `insights`. Each daily snapshot includes `explanation`; no chart configuration is returned. The existing `/health` endpoint remains unchanged.

## Verification

- Backend: `cd apps/api` and `.venv/bin/python -m pytest -W error`.
- Frozen data: `python3 -m unittest discover -s data/tests -v` from the repository root.
- Frontend: `npm run lint`, `npm run typecheck`, and `npm run build` from the repository root.

Tests cover each Bug lifetime, scope entry, closure and double-count prevention, causal reconciliation, configurable flatline boundaries, upward insights, determinism, input non-mutation, renamed IDs, altered event timing, same-day Bug creation/resolution, non-closure-blocking Bugs, and endpoint/domain equality. Synthetic variants exist only in memory; all frozen dataset digests remain unchanged.
