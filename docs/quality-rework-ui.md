# Quality & Rework presentation

The existing Quality & Rework route now renders the approved demo API. A typed server-side client uses `ADI_API_BASE_URL`, no-store fetch, and a ten-second timeout. It does not reconstruct events or calculate population, rates, cycles, or effort.

## Interface

`QualityReworkView` composes `QualitySummary`, `FirstPassQA`, `ReworkOverview` (with `ReworkStoryList`), and `ReworkEffortSection`. A shared `EffortValues` component displays totals and per-story effort. Server rendering is sufficient; no new client component or chart dependency is needed.

- Summary: project/backlog/sprint and the six requested quality indicators from the API.
- First-pass QA: a compact neutral horizontal ratio and explicit passed/eligible text. Percentage formatting uses the backend's precision, rounded to one decimal for display only. Null rates show Unavailable, not zero.
- Population detail: every active-scope story, its supplied outcome, eligibility, and carry-over context. Excluded client incidents and stories not reaching QA have concise explanations. Unknown outcomes remain undetermined.
- Rework: backend story/cycle/completed/active/Bug counts, followed by story-level cycles and final states. A purple accent and “Active rework” label identify active cycles without assigning risk or quality scores.
- Traceability: Bug IDs and event IDs for rejection/return, defect detection, successful QA certification, and resolution. Multiple cycles render separately; task effort stays at story level rather than being speculatively allocated across cycles.
- Effort: recorded task counts and estimated/completed/remaining hours. No normalization is applied when completed plus remaining exceeds estimates. This is not a productivity score or Capacity Health.

The page reuses unchanged Sprint Health CSS and adds styles scoped to `.quality-rework`. The application shell and other pages remain unchanged. Loading, unavailable, and empty states follow existing patterns. On narrow screens the population and cycle details stack, and indicator grids use two columns. Color is supplementary to text, never a health score.

The existing UI label “Rework acceptance” refers to the API’s successful QA certification evidence. It does not mean the User Story is fully completed; `Closed` remains the final completion boundary. No UI label or calculation is changed by this documentation clarification.

## Validation

Tests use a captured API response and modified presentation values to verify that the page does not recalculate backend results. Coverage includes all requested outcomes, population explanations, active/completed cycles, evidence, totals and per-story effort, null outcomes/rates, server fetching, and loading/error/empty states.

Desktop/mobile screenshots and browser checks use the real local API and production build. No release, deployment, or v0.2 capability is part of this task.


Verification completed: 59 frontend tests (25 new), 88 backend tests, and 21 frozen-fixture tests passed. Lint, TypeScript, and production build passed. Browser checks at 1440px desktop and 390px mobile verified readable ratio/evidence, no horizontal page overflow, no browser errors, and navigation across all three views after chart hydration. Byte comparisons confirmed 45 frozen-fixture, backend, shell, and existing UI source files remained unchanged.

Milestone status: **Feature complete — pending portfolio release preparation**. No Product Owner or UX decision remains for this slice.
