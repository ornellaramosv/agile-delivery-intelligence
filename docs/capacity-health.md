# Capacity Health — v0.2 Current Sprint

Capacity Health asks: **Can we still finish the remaining work with the capacity we have left?** It uses team-level DEV and QA hours, never individual rankings or utilization scores. The data foundation, pure domain engine, fixture service, and read-only API are implemented. The Current Sprint frontend is available at `/capacity-health`. Retrospective UI and the v0.2 release are not implemented.

## Capacity and progress

Burndown counts remaining delivery work items. Delivery Flow reports User Story positions. Quality & Rework explains QA returns and correction effort. Capacity Health compares remaining delivery **hours** with remaining effective DEV/QA capacity. These signals complement one another; their units and conclusions are not interchangeable. v0.1 contracts and frozen data remain unchanged.

The four pillars are:

- **Causal Capacity:** explain delivery, rework, new scope, support, regression, and technical effort separately.
- **Cross-sprint Release Readiness:** reconstruct an explicit release scope across sprints.
- **Adaptive Support Forecasting:** use weighted standard-case evidence plus known open work.
- **Critical Disruption Context:** expose extraordinary interruptions and actual evidence separately from standard forecasts.

Deterministic **What Changed** connects these facts to planning and the previous working day. No recommendations are generated.

## Sources and temporal evidence

All new records are fictional. They do not identify employees, employers, customers, or real incidents. The five [Sprint 08 v1 JSON files](../data/demo/sprint-08/) remain frozen. New files extend that scenario, not replace it; see the [schema](../data/schema.md#capacity-health-evidence-v02).

`task-capacity-map.json` stores only Task ID and discipline. `tasks.json` remains authoritative for estimates, final completed/remaining hours, and effort classification. Classification is mapped mechanically: `planned → baseline_delivery`, `rework → rework`, `scope_added → post_planning_scope`.

The new ledger supplies explicitly authored time entries and intermediate remaining-effort observations. These are raw temporal evidence, not stored capacity snapshots, forecasts, or gaps. Task time entries must reconcile exactly to frozen completed hours. They are never added a second time to the Task totals. At the final snapshot the engine uses the frozen Task values directly; earlier snapshots use only dated entries/observations available then. Before a remaining-effort observation, a created unfinished Task uses its original estimate. Completed Tasks have zero remaining effort. Later observations may revise effort upward; estimates are never normalized to completed plus remaining hours.

The schedule is 20 DEV h and 10 QA h per working day. End-of-day snapshots are at 18:00 UTC, matching this fixture's final observation. Planning is the frozen baseline timestamp. No interpolation of task progress occurs in application code. Historical observations are carried forward until superseded. Entries are team effort, not individual time sheets.

## Forecast, reserve, actual

A **forecast** is calculated from historical evidence. A **reserve** is a planning allocation. **Actual** is recorded effort. Differences are signed hours, not health labels.

For standard support, with recency weights summing to one:

```
forecasted_new_cases = Σ(period standard-case count × weight)
expected_hours_per_case = Σ(period standard effort / case count × weight)
forecast = forecasted_new_cases × expected_hours_per_case + planning open remaining
```

Critical cases are excluded from both historical count and effort. Periods explicitly marked complete with zero standard cases contribute zero to case frequency; they supply no hours-per-case observation. The approved weights are not redistributed to guess that missing rate. If any required weighted period lacks measurable case-effort evidence, the forecast is null; an observed count of zero remains distinct from absent history. Incomplete history also produces `insufficient_history`.

For regression:

```
expected_hours_per_scope_item = Σ(release actual QA hours / scope count × weight)
regression_forecast = current release scope count × expected_hours_per_scope_item
```

No active release means forecast/reserve/actual zero and `not_applicable`. DEV regression is also not applicable. An active release with no valid regression history has a null forecast and `insufficient_history`. Forecast status is separate from the primary answer.

```
planned_product_capacity = gross - support reserve - regression reserve
reserve_vs_forecast = reserve - forecast
actual_vs_reserve = actual - reserve
actual_vs_forecast = actual - forecast
```

Standard support actual is compared with the standard support forecast/reserve. Critical actual is exposed separately and included once in total support consumption. It does not consume the standard forecast residual. Engineering effort by other areas can be retained as case evidence without charging it to DEV or QA.

## Remaining capacity and the primary answer

At the end of working day t:

```
future_scheduled_capacity = Σ(gross scheduled hours for days > t)
remaining_standard_support = max(planning support forecast - standard actual, known open standard remaining, 0)
remaining_support = remaining_standard_support + known open critical remaining
remaining_regression = max(regression forecast - regression actual, observed regression remaining, 0)
remaining_technical = latest observed remaining technical effort for open dependencies
remaining_non_delivery = remaining_support + remaining_regression + remaining_technical
non_delivery_shortfall = max(remaining_non_delivery - future_scheduled_capacity, 0)
effective_remaining_capacity = max(future_scheduled_capacity - remaining_non_delivery, 0)
remaining_delivery = baseline remaining + rework remaining + post-planning remaining
capacity_gap = effective_remaining_capacity - remaining_delivery
capacity_pressure = remaining_delivery / effective_remaining_capacity  (only if capacity > 0)
```

Support and regression are not also included in delivery demand. Residual forecasts are not silently discarded when cases close or the sprint ends. Consequently Day 10 can show a non-delivery shortfall even when known support cases are engineering-closed.

An unavailable required forecast remains null. Its dependent effective capacity, gap, pressure, and uncovered demand remain null when not determinable. The response exposes known non-delivery demand as a lower bound and maximum possible delivery capacity as an upper bound. If that upper bound is zero, effective capacity is exactly zero even with unknown forecasts. Pressure is always null at zero effective capacity; no infinity is returned.

The Product Owner-approved primary answers are:

- `yes` when no delivery work remains, with that explicit reason, or when sufficient evidence covers every discipline with remaining delivery demand.
- `no` when any required discipline has a provable shortfall. Missing forecasts cannot reverse a shortfall proved by known demand. The reason uses **at least** when relevant.
- `insufficient_data` when missing evidence prevents either determination. `missing_inputs` names fields such as `DEV_SUPPORT_FORECAST`. This is not a warning, critical level, or other health state.

For example, with 25 delivery hours and 5 known support hours: 20 future hours proves a shortfall of at least 10 h even if the forecast is null; 40 future hours cannot justify a yes without that forecast.

Exact rational arithmetic is retained through calculations. Only the response boundary formats hours to at most two decimals and ratios to four. No intermediate forecast rounding occurs.

## Support lifecycle and scope conversion

Standard cases enter QA validation. A non-reproducible case can be engineering-closed. Reproducible technical issues may involve DEV/Architecture and become client-priority sprint work, then pipeline preparation for a future release and engineering closure. Product Owner approval is not a universal gate. Engineering closure and customer/support closure are separate facts; awaiting release can leave the customer-facing case open without leaving engineering work open.

`SUP-08-003` links to the frozen Day 6 `EVT-021` scope entry for US-111. Its 3 DEV/5 QA support hours occur before formal entry. The existing US-111 Tasks contribute 11 DEV/3 QA actual hours after entry as post-planning scope. They are not counted again as support. After conversion, remaining correction work belongs to those Tasks.

Critical incidents may bypass initial QA validation, engage required technical areas immediately, displace regular work, and produce an urgent package. Current critical case events, effort IDs, remaining effort and engineering status are surfaced in `critical_disruptions`; an active disruption does not replace the capacity answer. This Sprint 08 extension contains no current critical incident, preserving the specified standard-support and final actual totals. A fictional historical critical case demonstrates exclusion, and synthetic tests cover active critical behavior.

Original baseline stays at ten stories and 188 estimated hours. Scope rates compare one added story and 13 added estimated hours against that baseline, excluding rework from the baseline denominator. Added actual is 14 h. No “improvisation score” is produced.

## Release and dependencies

REL-08 contains six stories: three already certified/Closed in earlier sprints and current US-101, US-102, US-110. Other current stories target future releases. These additions are new fictional context, not edits to frozen workflow evidence.

Ready for Regression requires **all release-scoped stories Closed** and **all included customer cases Engineering Closed**. Current story states are replayed from frozen events. Earlier stories have dated closure/certification evidence. Customer closure is not a gate. DevOps, environments and pipelines are context, not extra readiness conditions.

Readiness is achieved on Day 7. Regression starts Day 8, consumes 6 h then 5 h on Day 9, and completes before sprint end. Later certification effort is explicitly recorded. The response exposes regression phase and whether QA has completed regression and can return to certification; it does not automatically assign work.

DEP-001 (pipeline/DevOps, US-107) records 3 DEV h and resolves Day 6. DEP-002 (Architecture, US-108) records 2 DEV h, remains open, and has 2 h observed technical demand remaining. Dependency elapsed time uses calendar timestamps, including nights/weekends. It is never converted to DEV effort. Overlapping dependencies retain separate evidence and observations; elapsed durations are never summed into capacity consumption.

## API and What Changed

`GET /demo/sprint-08/capacity-health`

Optional query parameters:

- `sprint_day=1..10`, default 10, selects the end-of-day observation.
- `comparison=since_planning|since_previous_working_day`, default `since_planning`. Day 1 compares with planning in either mode.
- `mode=current_sprint|retrospective`, default `current_sprint`, declares consumer intent without changing calculations.

The response contains `sprint`, `sprint_progress`, `mode_context`, `planning`, `disciplines`, `daily_capacity`, `release_readiness`, `scope_change`, `support`, `dependencies`, `critical_disruptions`, `what_changed`, `retrospective_breakpoints`, and `insights`. The primary answer is in `mode_context.primary_answer` and the capacity-answer insight. Daily capacity includes only days up to the requested snapshot.

`sprint_progress` summarizes the selected end-of-day Delivery Flow replay, without replaying workflow a second time. `original_baseline` and `current_scope` each expose `total`, `closed`, `open`, and `completion_rate` (a ratio, null for an empty population). `post_planning_scope` exposes `total`, `closed`, and `open`. Only Closed stories count as completed; scope-added stories appear only after their formal entry. Day 10 is 10/6/4 for baseline, 11/7/4 for current scope, and 1/1/0 for added scope (total/closed/open).

`release_readiness.summary` aggregates the existing release evidence: `total_scope_items`, `closed_scope_items`, `pending_scope_items`; `current_sprint_required_total`, `current_sprint_required_closed`, `current_sprint_required_pending`; and `included_customer_cases_total`, `included_customer_cases_engineering_closed`, `included_customer_cases_pending`. Current-sprint counts use the existing active required-story membership. Customer counts use engineering closure, not customer-facing closure. When no release is active, the summary is null alongside `status: not_applicable`. These summaries do not change readiness gates or capacity calculations.

`support.history` exposes the historical forecast periods in chronological start-date order. Each period includes `sprint_id`, `recency_weight`, `standard_case_count`, and `actual_hours` aggregated only from standard cases. Discipline keys are uppercase (`DEV`, `QA`, `ARCHITECTURE` where present); absent disciplines are omitted. Critical cases contribute neither counts nor hours. No history returns an empty list. This evidence accompanies forecast/reserve/actual values without changing any forecasting formula.

What Changed exposes net remaining-delivery and consumption differences plus dated evidence for task effort/remaining observations, QA returns, new scope, support events, regression, dependencies and critical interruptions. Final remaining observations reference the frozen Task IDs. It does not infer causality from correlations or manufacture recommendations. Retrospective breakpoints identify those major events and sign changes in a calculable capacity gap. Null gaps do not manufacture crossings.

Current Sprint uses these observations to answer the remaining-capacity question. Retrospective uses the same engine and evidence to explain prior turning points. No frontend calculations are needed for either mode.

## Verified fixture results

| Measure | DEV | QA |
| --- | ---: | ---: |
| Gross capacity | 200 h | 100 h |
| Support forecast / reserve | 12.60 / 13 h | 16.90 / 10 h |
| Regression forecast / reserve | 0 / 0 h (not applicable) | 8.38 / 9 h |
| Planned product capacity | 187 h | 81 h |
| Baseline actual | 118 h | 50 h |
| Rework actual | 38 h | 7 h |
| Post-planning actual | 11 h | 3 h |
| Support actual | 7 h | 10 h |
| Regression actual | 0 h | 11 h |
| Technical actual | 5 h | 0 h |
| Total actual | 179 h | 81 h |
| Final remaining delivery | 45 h | 0 h |
| Day 10 future / effective capacity | 0 / 0 h | 0 / 0 h |
| Day 10 capacity gap | −45 h | 0 h |
| Day 10 pressure | null | null |

Added scope: 10% by story count; 6.91% by estimated effort overall, 7.09% DEV and 6.38% QA. Day 10's answer is **no: DEV is short by 45 h**. Figures in this documentation are audit expectations, never engine constants.

## Current Sprint frontend

`/capacity-health` uses a typed server-side client with the existing API origin, no-store fetching and timeout. Native GET selectors send the selected Day 1–10 and comparison, always requesting `mode=current_sprint`. No metric is calculated in browser or frontend server code: counts, gaps, totals, answers, support history and release summaries come directly from the API.

The page prioritizes the backend answer and hour-based gap, keeps story progress separate, and presents DEV/QA side by side (stacked on mobile). Support forecast/reserve/actual and historical evidence have equal column prominence. Details expose change evidence, including post-planning story IDs. Critical context is conditional on active disruptions; release content is hidden when not applicable. Nulls display as unavailable, with no health colors or inferred recommendations. Loading, API-unavailable and empty states follow the established pages.

Targeted frontend tests cover presentation and request parameters; local desktop/mobile checks cover rendering and selectors. No full repository suite, deployment, tag or release is part of this slice.

## Non-goals

No Retrospective UI, SLA intelligence, individual productivity, rankings, aggregate health score, utilization score, good/bad labels, traffic-light thresholds, AI, recommendations, persistence, integrations, deployment, or release/tag creation. Capacity Health does not change Sprint Intelligence units or behavior.
