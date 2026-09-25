# Delivery Flow presentation

The Delivery Flow page consumes `GET /demo/sprint-08/delivery-flow` through a typed, server-side client. It uses the same `ADI_API_BASE_URL`, no-store policy, and bounded timeout as Sprint Health. The backend remains authoritative; frontend code neither replays events nor calculates flow metrics.

## Presentation

- `DeliveryFlowView` composes `FlowSummary`, `CurrentFlowComposition`, `FlowTimelineChart`, and `DailyFlowMovements`.
- The latest API snapshot supplies project/sprint context and active, Closed, and open story counts. Missing observations show Unavailable rather than zero.
- Current composition uses compact labeled state counts, including zero values. Names/order come from `workflow_states`; the frontend defines no second workflow enum.
- Recharts stacked bars show the backend's end-of-day state counts directly. They are discrete daily compositions, not a cumulative-flow diagram. A collapsible table provides exact daily counts and active scope without relying on hover or color.
- Muted categorical colors identify positions, not delivery health. QA → Returned to DEV has a purple accent and an explicit “QA return · Rework” label; it is not an employee-performance judgment.
- Daily movements retain Work Item and event IDs. Scope entries are separate from transitions. Day 6 displays US-111's entry and the API's 11 active stories, with an explicit unchanged-baseline note. Context events excluded by the backend are not reintroduced.
- Reuse the existing Sprint Health stylesheet unchanged; Flow-specific rules are scoped beneath `.delivery-flow`. The application shell, navigation, and Burndown components stay unchanged.
- Loading, unavailable, and empty states follow the existing page patterns. Only the chart needs a client-component boundary. No dependency is added.

## Verification

Presentation tests use a captured backend response, including modified values to guard against hardcoded totals. They cover metadata, current composition, scope entry, QA returns, excluded context, server fetching, and loading/error/empty states. Existing domain and fixture tests remain responsible for calculation correctness.

Desktop and mobile browser verification uses the real local API and production frontend. Screenshots are stored in `docs/screenshots/`. The chart is supplemented by exact accessible values, and movement text wraps on narrow screens.

No Quality & Rework features, risk algorithms, or additional product metrics are implemented. No Product Owner decision is required for this presentation slice.

Verified results for this slice: 34 frontend tests (16 new), 54 backend tests, and 21 fixture tests passed; lint, TypeScript, and production build passed. Browser checks at 1440px desktop and 390px mobile found no page overflow or browser errors. Navigation to Sprint Health and Quality & Rework and back succeeded. The mobile exact-value table scrolls within its own container. Byte comparisons confirmed all 35 monitored frozen-fixture, backend, and Sprint Health files remained unchanged.
