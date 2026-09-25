# Sprint Health — Burndown UI

The first frontend slice presents the existing `GET /demo/sprint-08/burndown` result. The frozen dataset and Burndown engine are unchanged. No domain calculation, health algorithm, or new insight type is implemented in the frontend.

## Interface

1. **Sprint summary:** project, backlog, sprint, available working-day snapshot count, date range, original baseline, and remaining work at the latest scenario day. The API has no overall Sprint Health status, so none is shown.
2. **Burndown:** Actual Remaining Work from each API snapshot and a dashed Original Baseline reference. The API has no expected/ideal trajectory. The fixed reference is explicitly labelled as not being an expected trajectory.
3. **Daily movement explanation:** all available days show previous and current remaining work, the backend delta and movement, and structured causes with IDs and event references. Previous remaining work is the preceding snapshot's value, not a frontend calculation. Day 1 shows no invented Day 0 comparison.
4. **Insights:** only backend Upward Movement and Flatline records are rendered. Movement styles use neutral blue, violet, and gray, with explicit text; colors are not health assessments.

Day 6 shows `11 → 11`, `Flat`, and `Net delta: 0` while preserving US-111 scope addition (+1, EVT-021) and US-110 closure (−1, EVT-024). No “nothing happened” interpretation replaces those causes. The same activity remains visible in the Days 5–6 Flatline insight.

## Components and data flow

```text
SprintHealthPage (server)
├── getSprintBurndown (typed API client)
└── SprintHealthView
    ├── SprintSummary
    ├── BurndownChart (client boundary)
    ├── DailyMovementList
    └── BurndownInsights
        └── CauseList (shared with daily explanations)
```

The client centralizes endpoint configuration and fetch behavior. TypeScript response types mirror backend output; readable labels are presentation mappings. The chart receives snapshots directly. Summary values come from the first/latest snapshot; no daily totals, movement classification, flatline detection, or ideal series are computed in the browser.

The server fetch uses `cache: "no-store"` and a 10-second timeout. `loading.tsx` supplies a visible loading state during the request. Request failures show an API-unavailable state with a normal reload link; no automatic retry system or fabricated data is used. Empty snapshots show an empty state and unavailable summary values rather than zero-valued metrics.

## Chart decision

There was no chart dependency. Use **Recharts 3.10.1** with its focused React line-chart components, responsive container, reference line, and accessible tooltip/navigation support. This avoids a custom SVG implementation and a full visualization/UI framework. Animations are disabled, and the surrounding layout uses plain CSS. The chart is the only interactive client component; summary, daily records, and insights are server-rendered.

The daily list supplies a readable alternative to the chart and preserves all actual values. The chart has a zero-based work-item axis, explicit units, day ticks, keyboard navigation, a labelled legend, and a fixed-baseline disclaimer. Mobile layouts keep daily causes visible rather than hiding them inside tooltips.

References: [Recharts](https://recharts.org/), [accessibility documentation](https://github.com/recharts/recharts/blob/main/storybook/stories/API/Accessibility.mdx).

## Local setup

Run the FastAPI application on port 8000 and the frontend on port 3000 as described in the root README. The Next.js server defaults to `http://127.0.0.1:8000` for the API. To change it, copy `apps/web/.env.example` to `apps/web/.env.local`, set `ADI_API_BASE_URL`, and restart the frontend. This is a server-only variable; no public API URL, proxy route, or backend CORS changes are needed.

A production build does not require the API to be running; Sprint Health is rendered dynamically when requested. At runtime, the API must be reachable from the Next.js server.

## Testing

`npm test` runs Vitest with React Testing Library and jsdom. Tests cover metadata, all ten snapshot rows, the Day 3–6 movement labels, opposing Day 6 causes, insight detail, loading, empty/API failure states, and the server page/client boundary. Chart measurement is fixed in jsdom while the real Recharts components render. Browser verification covers actual responsive sizing and live API rendering.

`tests/fixtures/burndown.json` is a captured endpoint response for presentation tests; it is not an application data source or a replacement for the frozen scenario. No domain calculations are reproduced in the tests. The payload was captured by calling `app.services.demo_burndown.sprint_08_burndown()` from the API workspace and serializing its returned JSON. If the API contract changes, recapture this presentation fixture; do not modify frozen scenario records to accommodate UI tests.

## Product Owner review

The backend does not expose an expected/ideal trajectory. Defining that domain rule and adding an expected series requires a future Product Owner decision and backend task. This slice uses the authorized Original Baseline reference fallback. No overall Sprint Health status is inferred or requested from the user.

## Verified result

- 18 frontend presentation/client tests passed.
- 31 backend tests and 21 frozen-data validations passed; no domain or scenario files changed.
- Frontend lint, TypeScript, and production build passed. Identical duplicate generated `.next/types/* 2.ts` cache files caused a local TypeScript conflict; those duplicates were removed without changing source configuration.
- The live server page fetched the existing API successfully (HTTP 200), rendered ten daily rows, and showed the expected Day 6 causes. Browser console/page error checks were clear.
- Desktop at 1280px and mobile at 390px were checked. Mobile document width equalled viewport width, and causal detail remained visible. Keyboard chart navigation exposed Day 2 / 9 remaining items in the tooltip.
- Stopping the test API produced the unavailable state; restoring it and selecting Try again recovered the live page. Home-to-Sprint-Health navigation also passed.

Screenshots: [desktop](screenshots/sprint-health-desktop.png), [Day 6 on mobile](screenshots/sprint-health-day6-mobile.png).
