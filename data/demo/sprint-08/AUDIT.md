# Sprint 08 — Product audit

**Atlas / Core Services · April 8–19, 2030 · final snapshot: Day 10, 18:00 UTC.**

All records are fictional. This dataset is designed to test delivery-intelligence behavior, not employee performance. This is a static review of the JSON fixture, not an application metric or Capacity Health implementation.

## Dataset freeze

**Dataset version: v1 — frozen for Sprint Intelligence implementation**

Frozen story IDs, bug IDs, dates, workflow events, task effort, initial states, final states, baseline membership, and scope-added membership must not change during Sprint Intelligence implementation unless a Product Owner-approved defect is discovered. The validation suite pins the semantic contents of all five JSON files with SHA-256 digests (formatting and object-key order are ignored). Do not refresh these digests to accommodate implementation changes; an approved dataset defect is required.

## Confirmed semantics

- **Original Baseline:** US-101–US-110, fixed at 10 User Stories. US-111 enters separately on Day 6; baseline membership never changes.
- **Burndown unit:** remaining delivery work items, not hours. Original Baseline and Current Remaining Work are separate. An open Bug with `blocks_story_closure = true` represents additional delivery work and may increase Current Remaining Work. An open, formally scope-added User Story also represents additional delivery work; original baseline membership is unchanged. This audit does not calculate Burndown or a daily remaining-work series.
- **Source:** work origin, limited to `roadmap` and `client_incident`. Carry-over is independent: US-110 remains roadmap + carry-over.
- **Effort kind:** reason for Task effort, limited to `planned`, `rework`, and `scope_added`. US-111 tasks are scope added; defect-driven fixes, recertification, and associated integration are rework. Hours belong to Task effort and future Capacity Health.

## User Story audit

Initial state means the Day 1 opening snapshot for baseline stories, or the Day 6 entry state for US-111. QA is already on its first attempt for US-101–US-104 at sprint opening. Failed first attempts remain failures even when recertification later passes. A rework cycle is a traceable QA rejection requiring DEV work; it need not finish within the sprint.

| ID | source | Original baseline | Scope added | Carry-over | Initial state | Final state | First QA attempt outcome | Rework cycles | Related bug | Close day |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| US-101 | roadmap | Yes | No | No | QA | Closed | Passed | 0 | None | Day 2 |
| US-102 | roadmap | Yes | No | No | QA | Closed | Failed | 1 | BUG-001 | Day 7 |
| US-103 | roadmap | Yes | No | No | QA | Closed | Passed | 0 | None | Day 8 |
| US-104 | roadmap | Yes | No | No | QA | Returned to DEV | Failed | 1 | BUG-002 | Open |
| US-105 | roadmap | Yes | No | No | Development | Closed | Failed | 1 | BUG-003 | Day 10 |
| US-106 | roadmap | Yes | No | No | Development | Closed | Passed | 0 | None | Day 10 |
| US-107 | roadmap | Yes | No | No | Development | Code Integration | Not reached | 0 | None | Open |
| US-108 | roadmap | Yes | No | No | Development | Development | Not reached | 0 | None | Open |
| US-109 | roadmap | Yes | No | No | Development | Development | Not reached | 0 | None | Open |
| US-110 | roadmap | Yes | No | Yes | Ready for QA | Closed | Passed | 0 | None | Day 6 |
| US-111 | client_incident | No | Yes | No | Development | Closed | Passed | 0 | None | Day 10 |

US-111 passes QA but remains excluded from the future normal-roadmap first-pass QA population because it is added client-incident scope. No QA rate is calculated here. US-107–US-109 do not reach QA.

## Bug audit

| Bug ID | Related US | Creation day | Resolution day / status | blocking (legacy) | blocks_story_closure | Resulting rework cycle |
| --- | --- | --- | --- | --- | --- | --- |
| BUG-001 | US-102 | Day 3 | Day 7 / Closed | No | true | 1: QA → Returned to DEV on Day 3 (EVT-015); recertified and closed |
| BUG-002 | US-104 | Day 4 | Unresolved / Open at sprint end | Yes | true | 1: QA → Returned to DEV on Day 4 (EVT-017); unfinished at sprint end |
| BUG-003 | US-105 | Day 7 | Day 10 / Closed | No | true | 1: QA → Returned to DEV on Day 7 (EVT-028); recertified and closed |

`blocks_story_closure` is a required boolean. When true, the related User Story cannot reach final completion at `Closed` while the Bug is unresolved; the story may return to Development, and the open Bug represents additional delivery work that future Burndown logic may count as one additional unit. When false, the Bug does not prevent story closure and must not automatically increase Current Remaining Work. This permits future Consideration/deferred-work cases without implementing them here.

The existing `blocking` field is retained unchanged as the original fixture's “blocking defect” marker (true only for BUG-002). It is a different concept from `blocks_story_closure`; it is not the criterion for story acceptance or Current Remaining Work. No new criticality or release-gating meaning is assigned to that legacy field. All three Sprint 08 Bugs have `blocks_story_closure = true` because all three caused QA rejection and return to DEV.

US-104 correctly remains Returned to DEV with BUG-002 Open. Bug resolution here means QA-verified closure, not merely completion of a Bug Fix task. A `qa_passed` event records successful recertification execution; final User Story completion occurs at its later `closed` event, after bug resolution. This does not assign product-acceptance ownership universally to QA.

## Task-effort audit

Hours are summed directly from the final Task snapshots for review only. Original estimates remain unchanged. Completed hours are cumulative effort consumed, including on unfinished tasks; remaining hours are the latest estimates. Completed plus remaining hours need not equal the original estimate. No productivity, capacity, or Burndown measure is inferred.

| effort_kind | Number of tasks | Estimated hours | Completed hours | Remaining hours |
| --- | --- | --- | --- | --- |
| planned | 15 | 188 | 168 | 37 |
| rework | 7 | 45 | 45 | 8 |
| scope_added | 3 | 13 | 14 | 0 |
| **Total** | **25** | **246** | **227** | **45** |

- Planned: original baseline effort; no baseline task was relabeled as scope added.
- Rework: TASK-003–005 for BUG-001, TASK-008 for BUG-002, and TASK-012–014 for BUG-003. Each has a preceding linked QA rejection event.
- Scope added: TASK-023–025, all belonging to US-111 and created after its Day 6 acceptance.
- A Closed QA Certification task can record an unsuccessful test execution; the story still requires its own QA pass and Closed event.

## Day-by-day delivery history

All times below are UTC. Event IDs refer to `delivery-events.json`. Context events retain the story state; they are not extra workflow transitions.

### Day 1 — 2030-04-08

- 09:00: record the immutable baseline and opening states. US-101–US-104 are in QA; US-105–US-109 are in Development; carry-over US-110 is Ready for QA. US-111 is not yet in the sprint. These are opening snapshots, not new QA attempts (EVT-001–EVT-010).

### Day 2 — 2030-04-09

- 10:00 — **US-110:** Ready for QA → QA; first QA certification begins. (EVT-011)
- 14:30 — **US-101:** First QA certification passes. (EVT-012)
- 15:00 — **US-101:** QA → Closed; User Story accepted. (EVT-013)

### Day 3 — 2030-04-10

- 10:00 — **US-102:** QA detects BUG-001 (`blocking = false`; `blocks_story_closure = true`). (EVT-014)
- 10:05 — **US-102:** QA → Returned to DEV for BUG-001; one rework cycle begins. (EVT-015)

### Day 4 — 2030-04-11

- 11:00 — **US-104:** QA detects BUG-002 (`blocking = true`; `blocks_story_closure = true`). (EVT-016)
- 11:05 — **US-104:** QA → Returned to DEV for BUG-002; one rework cycle begins. (EVT-017)
- 12:00 — **US-105:** Development → Code Integration. (EVT-018)

### Day 5 — 2030-04-12

- 11:00 — **US-105:** Code Integration → Ready for QA. (EVT-019)

### Day 6 — 2030-04-15

- 09:00 — **US-105:** Ready for QA → QA; first QA certification begins. (EVT-020)
- 09:30 — **US-111:** Client incident validated and formally added in Development; original baseline unchanged. (EVT-021)
- 11:30 — **US-110:** First QA certification passes. (EVT-022)
- 12:00 — **US-102:** Returned to DEV → Code Integration after the BUG-001 fix. (EVT-023)
- 12:00 — **US-110:** QA → Closed; User Story accepted. (EVT-024)
- 15:00 — **US-102:** Code Integration → Ready for QA for BUG-001 recertification. (EVT-025)

### Day 7 — 2030-04-16

- 09:00 — **US-102:** Ready for QA → QA; recertification for BUG-001 begins. (EVT-026)
- 11:00 — **US-105:** QA detects BUG-003 (`blocking = false`; `blocks_story_closure = true`). (EVT-027)
- 11:05 — **US-105:** QA → Returned to DEV for BUG-003; one rework cycle begins. (EVT-028)
- 12:00 — **US-106:** Development → Code Integration. (EVT-029)
- 14:00 — **US-102:** QA recertification for BUG-001 passes. (EVT-030)
- 14:10 — **US-102:** BUG-001 resolution verified; bug Closed. Story remains in QA until acceptance. (EVT-031)
- 15:00 — **US-102:** QA → Closed; User Story accepted. (EVT-032)

### Day 8 — 2030-04-17

- 11:00 — **US-106:** Code Integration → Ready for QA. (EVT-033)
- 14:00 — **US-111:** Development → Code Integration. (EVT-034)
- 15:00 — **US-103:** First QA certification passes. (EVT-035)
- 16:00 — **US-103:** QA → Closed; User Story accepted. (EVT-036)

### Day 9 — 2030-04-18

- 09:00 — **US-106:** Ready for QA → QA; first QA certification begins. (EVT-037)
- 10:00 — **US-111:** Code Integration → Ready for QA. (EVT-038)
- 11:00 — **US-111:** Ready for QA → QA; first QA certification begins. (EVT-039)
- 12:00 — **US-105:** Returned to DEV → Code Integration after the BUG-003 fix. (EVT-040)
- 15:00 — **US-105:** Code Integration → Ready for QA for BUG-003 recertification. (EVT-041)

### Day 10 — 2030-04-19

- 09:00 — **US-105:** Ready for QA → QA; recertification for BUG-003 begins. (EVT-042)
- 11:00 — **US-107:** Development → Code Integration. (EVT-043)
- 14:00 — **US-105:** QA recertification for BUG-003 passes. (EVT-044)
- 14:10 — **US-105:** BUG-003 resolution verified; bug Closed. Story remains in QA until acceptance. (EVT-045)
- 15:00 — **US-105:** QA → Closed; User Story accepted. (EVT-046)
- 15:30 — **US-106:** First QA certification passes. (EVT-047)
- 16:00 — **US-106:** QA → Closed; User Story accepted. (EVT-048)
- 16:30 — **US-111:** First QA certification passes. (EVT-049)
- 17:00 — **US-111:** QA → Closed; User Story accepted. (EVT-050)
- 18:00 snapshot: US-104 remains Returned to DEV with BUG-002 Open; US-107 remains Code Integration; US-108 and US-109 remain Development. All other stories are Closed. This snapshot adds no new workflow event.

## Review findings

- Corrected the superseded origin label `backlog` to `roadmap` for US-101–US-110; the separate backlog name remains Core Services.
- Reclassified only US-111 tasks from `planned` to `scope_added`. Task hours, task estimates, baseline membership, bug records, and delivery events were preserved.
- Removed the earlier unresolved question about an hours-based Burndown: v0.1 uses remaining delivery work items.
- Added `blocks_story_closure = true` to BUG-001, BUG-002, and BUG-003. Their legacy `blocking` values remain false, true, and false respectively. All other JSON scenario data is preserved.
- No outstanding Product Owner decision remains for this correction. Sprint 08 is frozen as dataset v1.

## Evidence and validation

Sources: [sprint](sprint.json), [stories](work-items.json), [tasks](tasks.json), [bugs](bugs.json), [events](delivery-events.json), and [schema](../../schema.md). The tables and chronology are static audit documentation and must be refreshed if the fixture changes.

Run `python3 -m unittest discover -s data/tests -v` from the repository root for the fixture validations, including allowed enums, immutable baseline flags, US-110 carry-over/source, US-111 source/scope, prior linked QA rejection evidence for every rework task, boolean story-closure flags, and frozen v1 JSON content.
