# Milestones

## v0.1.0 — Sprint Intelligence

**Released — stable**

- Burndown Intelligence — domain engine, read-only demo endpoint, and first Sprint Health UI implemented; chart shows Actual Remaining Work and an Original Baseline reference
- Delivery Flow — domain engine, read-only demo endpoint, and workflow composition UI implemented
- First-pass QA — domain engine, read-only demo endpoint, and Quality & Rework UI implemented
- Rework Intelligence — domain engine, read-only demo endpoint, and Quality & Rework UI implemented

Repository foundation and the frozen Sprint 08 v1 dataset are complete. Burndown reconstructs daily delivery work, explains event causes, and returns upward/flatline domain insights. Sprint Health presents that API result as a chart, daily explanations, and insights; an expected trajectory is not provided by the backend. Delivery Flow reconstructs daily User Story positions and movements from events; its frontend shows current composition, daily stacked bars, and traceable movements. First-pass QA and Rework Intelligence now expose domain results through a read-only demo endpoint; the Quality & Rework UI now presents population, QA outcomes, cycle evidence, and recorded effort. See [Quality & Rework documentation](quality-rework-intelligence.md). See [Delivery Flow documentation](delivery-flow-intelligence.md). See [engine documentation](burndown-intelligence.md).

Flatline semantics are Product Owner-confirmed: only consecutive zero-delta days qualify. Upward days are separate. Sprint 08's default Flatline remains Days 5–6 at 11 remaining delivery work units; no Flatline decision remains pending.

All frontend/backend/data tests, lint, TypeScript, production build, and desktop/mobile browser checks passed for this milestone. v0.1 is released and remains stable during v0.2 work; no release or deployment is part of the Capacity Health backend task.

## v0.2.0 — Capacity Health

Backend foundation implemented: additive fictional evidence, pure domain engine, read-only `/demo/sprint-08/capacity-health` endpoint, deterministic What Changed and missing-evidence handling. Four pillars: Causal Capacity, Cross-sprint Release Readiness, Adaptive Support Forecasting, Critical Disruption Context. See [Capacity Health](capacity-health.md).

The Capacity Health **Current Sprint frontend is implemented** at `/capacity-health`, with server-side API consumption, day/comparison selection and responsive evidence views. Retrospective UI is not implemented. No v0.2 release or tag has been created. v0.1 engines, contracts, UI and frozen source files remain unchanged.

## Future milestones

- Impediment Intelligence
- Alerts and Scrum Master management
- Portfolio Intelligence
- Carry-over Intelligence
- Release Readiness
