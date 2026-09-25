# Foundation technical decisions

- Use the existing workspace and Git repository as the monorepo root; the package name is `agile-delivery-intelligence`. No nested repository is needed.
- Use npm workspaces for `apps/web` and standard Python `venv`/pip for `apps/api`. No additional monorepo orchestration is needed for two independent applications.
- Use Next.js App Router, TypeScript strict mode, server components, plain CSS, and system fonts. All three Sprint Intelligence navigation destinations now have implemented server-rendered pages.
- Pin ESLint 9.39.5 for compatibility with Next.js's React lint plugin. ESLint 10 failed when loading `react/display-name` during verification. npm marks ESLint 9 as deprecated; revisit the pin when the plugin supports ESLint 10.
- Keep API consumption centralized. Each Sprint Intelligence page fetches its read-only demo result on the Next.js server.
- Separate FastAPI application composition from the health router. Use pytest and FastAPI's TestClient for the single endpoint test. Retain FastAPI's default API documentation.
- Use Node.js 24+ and Python 3.14+ as the documented development baseline, matching the available runtimes used for verification.
- Record exact frontend dependencies in `package-lock.json` and pin direct backend dependencies in requirements files. Python transitive dependencies remain resolver-managed. Keep Python testing dependencies separate from runtime dependencies; the current Starlette TestClient uses `httpx2`.
- Keep fictional scenario data as separate human-readable JSON files under `data/demo/sprint-08/`. Use string identifiers and UTC timestamps, a fixed baseline membership list, final snapshots, and traceable workflow events. Demo services consume the fixture through pure domain engines. See its README and `data/schema.md` for data conventions and future modeling questions.
- Validate the fixture with Python standard-library `unittest` under `data/tests/`, independently of FastAPI and without adding dependencies. Fixture assertions do not implement product metrics.
- Preserve `.github/` with an empty `.gitkeep`; no remote resources or automation are configured in this task.

Framework references: [Next.js installation](https://nextjs.org/docs/app/getting-started/installation), [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/).

## Confirmed Sprint 08 / v0.1 data semantics

- Burndown's unit is remaining delivery work items. Hours belong to Task effort and future Capacity Health. No hours-based Burndown is planned for v0.1.
- Original Baseline stays fixed at 10 User Stories. Current Remaining Work is separate: an open Bug with `blocks_story_closure = true` or an open, formally scope-added User Story represents additional delivery work and may increase Current Remaining Work. Document this rule without implementing a calculation.
- `source` describes origin and allows only `roadmap` and `client_incident`. US-101–US-110 use `roadmap`; US-111 uses `client_incident`. Carry-over remains an independent flag on US-110.
- `effort_kind` describes why Task effort is consumed and allows only `planned`, `rework`, and `scope_added`. Normal baseline work is planned; defect-driven fixes, recertification, and associated integration are rework; all US-111 tasks are scope added. It is not an employee-productivity classification.
- Preserve original baseline membership, task estimates/hours, and event history when applying these label changes. Validate rework against prior linked QA rejection events, not task labels alone.
- Keep `AUDIT.md` as a static human-readable review artifact derived from the JSON fixture. Its grouped Task-hour totals are an audit aid only. No production aggregation service, Capacity Health logic, or application metrics are introduced.

## Bug story-closure semantics and dataset freeze

`blocks_story_closure` is a required boolean. When true, the related User Story cannot reach final completion at `Closed` while the Bug is unresolved; the story may return to Development, and the open Bug represents additional delivery work that future Burndown logic may count as one additional unit. When false, the Bug does not prevent story closure and must not automatically increase Current Remaining Work. This permits future Consideration/deferred-work cases without implementing them here.

The existing `blocking` field is retained unchanged as the original fixture's “blocking defect” marker (true only for BUG-002). It is a different concept from `blocks_story_closure`; it is not the criterion for story acceptance or Current Remaining Work. No new criticality or release-gating meaning is assigned to that legacy field. All three Sprint 08 Bugs have `blocks_story_closure = true` because all three caused QA rejection and return to DEV.

An open Bug with `blocks_story_closure = true` represents additional delivery work and may increase Current Remaining Work. When `blocks_story_closure = false`, future Burndown logic must not automatically add the Bug to Current Remaining Work. No calculation is implemented.

**Dataset version: v1 — frozen for Sprint Intelligence implementation**

Frozen story IDs, bug IDs, dates, workflow events, task effort, initial states, final states, baseline membership, and scope-added membership must not change during Sprint Intelligence implementation unless a Product Owner-approved defect is discovered. The validation suite pins the semantic contents of all five JSON files with SHA-256 digests (formatting and object-key order are ignored). Do not refresh these digests to accommodate implementation changes; an approved dataset defect is required.

## Burndown Intelligence Engine

- Use a pure Python domain function under `app/domain/burndown`, a filesystem-loading service under `app/services`, and a thin read-only `/demo/sprint-08/burndown` route. No new dependencies or persistence are required.
- Replay ordered workflow and Bug lifecycle events, rather than final snapshot states. Match Bug event timestamps to Bug records and reject inconsistent histories. Do not load Task hours.
- Retain structured positive and negative causes separately; reconcile their sum with the daily delta. Day 1 establishes the observation baseline and has null delta/movement. Sort IDs and timestamp/event-ID order for deterministic results without mutating inputs.
- Include component counts and contributing IDs. `active_rework_bugs` lists unresolved Bugs with prior QA-rejection evidence; it is context, not an extra remaining-work contribution.
- Configure the flatline threshold with the immutable `BurndownConfig` setting (default 2). The Product Owner has confirmed that flatlines contain only consecutive `delta == 0` days; `delta > 0` is Upward Movement and breaks the streak. Negative deltas are Down. The existing engine already follows this rule and requires no business-logic change. Emit one maximal run and preserve its daily causes and workflow event IDs. The Flatline decision is resolved; a possible future No Reduction Streak is a separate, unimplemented concept. See [Burndown Intelligence](burndown-intelligence.md) for the exact convention.
- Keep the frozen v1 JSON and its validation digests unchanged. Domain tests vary records only in memory. Tests compare the read-only endpoint with direct domain execution.
- Earlier notes describing semantic documentation without a calculation record the pre-engine milestone. The implementation described here now applies those confirmed semantics; no other product calculation is introduced.

## Sprint Health frontend slice

- Use a typed server-side API client with no-store fetch and a bounded timeout. Keep the backend/domain engine authoritative and unchanged; do not read scenario JSON directly in application UI code.
- Use Recharts 3.10.1 for a responsive line chart, with a dashed Original Baseline reference. The backend provides no expected trajectory or overall health status, so neither is invented. The expected-series rule remains a future Product Owner/backend decision.
- Keep plain CSS and the existing shell. Server-render the summary, daily explanations, and insight sections; isolate Recharts behind a small client component. Neutral movement colors do not encode health judgments.
- Render backend causes independently from net delta. Keep work-item, Bug, and event IDs visible. Show loading, API-unavailable, and empty states without fallback metrics or automatic retries.
- Add Vitest/React Testing Library presentation tests with a captured API response; use the real chart with fixed container measurements in jsdom. Browser verification exercises the actual API-to-page flow and responsive chart. See [Sprint Health UI](sprint-health-ui.md).


## Delivery Flow Intelligence Engine

- Follow the existing domain/service/router separation with a pure Python replay function, a small fixture loader, and `/demo/sprint-08/delivery-flow`. Keep the stable Burndown engine and loader unchanged; no new dependencies are needed.
- Read opening states and formal scope entry from Delivery Events, never final Work Item states. Validate chronology, references, baseline membership, and transition continuity. Replay timestamp/event-ID order deterministically without mutating inputs.
- Count active-scope User Stories only, including Closed stories. Bugs and Task effort are not Flow inputs. Return all seven normalized state counts plus per-story states so each daily distribution can be audited.
- Represent scope entries separately from movements: null-to-state opening/entry records activate scope; movements contain only changes between approved states. Preserve event IDs and timestamps for both. Same-state and null/null context records do not move stories.
- Add no Flow frontend or scoring. Frozen fixture bytes and validation digests remain unchanged. See [Delivery Flow Intelligence](delivery-flow-intelligence.md) for response fields, reconstructed results, and boundaries. No Product Owner decision is pending for this slice.


## Delivery Flow frontend slice

- Consume the approved API via a typed server client, keeping fetching, types, and presentation separate. Reuse existing Recharts and Sprint Health CSS unchanged; add scoped Flow styles only.
- Use compact state counts for current composition and stacked bars for discrete end-of-day snapshots, with a collapsible exact-value table. Render state names/order from the API; categorical colors encode no health judgment.
- Render the supplied movements and scope entries without event reconstruction. Label QA returns as rework and explain that scope entry leaves the original baseline unchanged.
- Preserve domain engines, frozen fixture, application shell, and Burndown UI. Test presentation from a captured API response and verify desktop/mobile against the live local API. See [Delivery Flow UI](delivery-flow-ui.md). No pending Product Owner decision for this slice.


## Quality & Rework Intelligence Engine

- Add a pure domain function, separate fixture-loading service, and thin read-only `/demo/sprint-08/quality-rework` route. Reuse Delivery Flow's validated replay without modifying it to establish scope and final workflow state.
- Apply the v0.1 roadmap/reached-QA population, including carry-over and first-attempt opening QA evidence. Exclude client incidents only from first-pass QA. Retain the first explicit QA certification/rejection outcome independently of eventual closure.
- Model 0..N cycles from QA → Returned to DEV transitions. Preserve rejection, defect detection, recertification, successful certification, and resolution evidence. A cycle completes upon a successful QA certification event after re-entry to QA; Bug resolution alone is a separate observation. Repeated cycles awaiting successful certification remain independently traceable.
- Sum Task effort only by the explicit rework classification, preserving overruns and contributing Task IDs. Do not allocate effort speculatively across cycles or infer cycles from Tasks/Bugs.
- Return an unrounded ratio, null for an empty denominator, and null outcome/reason for an attempt without outcome evidence. Do not invent a successful QA result from Closed alone. Document these missing-evidence conventions in [Quality & Rework Intelligence](quality-rework-intelligence.md).
- No dependencies, frontend changes, individual metrics, health thresholds, or other product capabilities are introduced. Test synthetic multi-cycle histories in memory; preserve frozen fixture bytes and digests.


## Quality & Rework frontend slice

- Consume the approved endpoint through a typed server-side client using the existing API origin, no-store policy, and timeout. Preserve all domain logic and original frontend slices.
- Present the backend ratio with native horizontal meter semantics and neutral styling, paired with passed/eligible text. Format the supplied ratio to one decimal percentage without recomputing it. Keep unknown outcomes and null rates explicit.
- Render all active-scope story classifications and eligibility explanations. Render each rework cycle separately with meaningful Bug/event evidence and a plain Active rework or Completed label. Show task effort at story and sprint levels without normalization or per-cycle allocation.
- Reuse existing page styles unchanged and add scoped CSS only. Server rendering needs no new dependencies or chart code. Test presentation against a captured API response and verify desktop/mobile against the local production app.
- v0.1.0 is Feature complete — pending portfolio release preparation after all checks passed. No release or deployment is performed. See [Quality & Rework UI](quality-rework-ui.md).


## Portfolio presentation preparation

- Public presentation uses the existing desktop captures, relative documentation links, and an explicit fictional-data statement. The README describes only the three implemented v0.1 slices and clearly separates planned exploration.
- Confirmed publication decision: no open-source license is granted at this stage; no LICENSE file is added.
- QA performs certification/validation. `qa_passed` records certification success; `closed` records the final completed story state. Existing quality API acceptance-named fields and cycle-completion calculations remain unchanged. No universal claim about organizational product-acceptance ownership is implied.
- Prepare the local unborn branch as `main` and use the approved author name. Author email still requires confirmation before any first commit; no email is invented or changed. No commit, remote, release, or deployment is part of this preparation.
