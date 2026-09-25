# Milestones

## v0.1.0 — Sprint Intelligence

**Feature complete — pending portfolio release preparation**

- Burndown Intelligence — domain engine, read-only demo endpoint, and first Sprint Health UI implemented; chart shows Actual Remaining Work and an Original Baseline reference
- Delivery Flow — domain engine, read-only demo endpoint, and workflow composition UI implemented
- First-pass QA — domain engine, read-only demo endpoint, and Quality & Rework UI implemented
- Rework Intelligence — domain engine, read-only demo endpoint, and Quality & Rework UI implemented

Repository foundation and the frozen Sprint 08 v1 dataset are complete. Burndown reconstructs daily delivery work, explains event causes, and returns upward/flatline domain insights. Sprint Health presents that API result as a chart, daily explanations, and insights; an expected trajectory is not provided by the backend. Delivery Flow reconstructs daily User Story positions and movements from events; its frontend shows current composition, daily stacked bars, and traceable movements. First-pass QA and Rework Intelligence now expose domain results through a read-only demo endpoint; the Quality & Rework UI now presents population, QA outcomes, cycle evidence, and recorded effort. See [Quality & Rework documentation](quality-rework-intelligence.md). See [Delivery Flow documentation](delivery-flow-intelligence.md). See [engine documentation](burndown-intelligence.md).

Flatline semantics are Product Owner-confirmed: only consecutive zero-delta days qualify. Upward days are separate. Sprint 08's default Flatline remains Days 5–6 at 11 remaining delivery work units; no Flatline decision remains pending.

All frontend/backend/data tests, lint, TypeScript, production build, and desktop/mobile browser checks passed for this milestone. Release creation and deployment await a separate Product Owner-approved preparation task.

## Future milestones

- Capacity Health
- Impediment Intelligence
- Alerts and Scrum Master management
- Portfolio Intelligence
- Carry-over Intelligence
- Release Readiness
