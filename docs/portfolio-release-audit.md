# v0.1.0 portfolio release audit

Audit date: 2026-09-25. Milestone: **Feature complete — pending portfolio release preparation**.

**Historical audit — subsequent preparation update:** The Product Owner has since decided to publish without granting an open-source license. The README now carries that notice, screenshots, architecture, and fictional-data guidance; QA terminology has been clarified without changing calculations. The local unborn branch is now `main`, and the approved author name is configured. Author email confirmation and the separately authorized first commit remain pending. The original audit findings below are retained as historical evidence, not a current request to select a license.

## Assessment and priorities

The implementation is suitable for portfolio preparation, but the repository is not ready for immediate public release. All current checks pass and no credentials were detected. Licensing and an intentional initial publication snapshot remain outstanding. This audit is not a guarantee that every possible security issue has been excluded.

### BLOCKER

- No public license decision has been made. Resolve that publication decision before release; no license was selected or added.
- There is no initial commit: zero tracked files and no commit history. A reviewed initial commit is necessary before there is a versioned portfolio repository to publish. No commit was made by this audit.

### SHOULD FIX

- Add a prominent fictional-demo statement, selected screenshots, a compact architecture/data-flow explanation, and a concise validation summary to the README. Existing information is accurate but requires too much scrolling and cross-document reading.
- Review intended author/committer identity before the first commit. Effective identity is configured outside repository-local configuration; its values are intentionally not reproduced here.
- Publish only the reviewed branch, not a mirror/archive of the local Git directory. Local Codex tree refs and unreferenced objects retain older documentation with the removed employer disclaimer. They are not normal commit history; no credentials or personal paths were detected in the object scan. No refs or objects were deleted.
- Reconcile terminology in the frozen audit versus quality documentation: `qa_passed` is certification evidence and cycle completion in the engine, while final story acceptance is described at `closed` in the scenario audit. Distinguish those concepts clearly; changing the cycle-completion rule requires Product Owner approval. Current fixture totals agree and no behavior was changed.
- Document/enforce the chosen Python runtime and consider a reproducible transitive dependency lock in a separately approved engineering task. Python 3.14+ is documented but not declared as `requires-python`; direct dependencies are pinned, transitive resolution is not.

### NICE TO HAVE

- CI for the existing commands, a compact contributor guide, and a documentation index.
- Consolidate historical decision notes and repeated freeze/semantics explanations without deleting substantive records.
- Curate the screenshot gallery and update the minor outdated population-description wording visible in the Quality mobile capture during later presentation work. No screenshot is broken.

### PRODUCT OWNER DECISION

- License decision required before public release. A license states the permissions and conditions for reuse; none was chosen here.
- Approve the public identity, final README presentation, repository visibility, and later publication/release preparation.
- Clarify acceptance terminology if desired; any change to cycle completion remains a separate product decision, not a hygiene fix.

## Security, privacy, fictional records, and local paths

Because `git ls-files` is empty, the audit covered all 106 initial publication candidates from tracked plus non-ignored untracked files, including hidden configuration and the lockfile. Text scans checked credentials, private-key/token patterns, emails, personal paths, employer references, and URL hosts. Git-local configuration and available object contents were also inspected without displaying identity/secret values.

No API keys, passwords, tokens, private connection strings, personal email addresses, personal filesystem paths, or private service URLs were detected in publication candidates. `.env.example` contains only the local API URL. URLs are public package/documentation hosts, loopback development endpoints, and a reserved test hostname. Installed dependencies and generated caches are not publication candidates.

One employer-name reference appeared only in the fictional-data README disclaimer. It was replaced with a generic fictional-data statement. No business record changed. No employer-name or personal-path matches remain in the publication candidates. Historical local snapshot objects still retain the older disclaimer as described above.

Atlas, Core Services, Sprint 08, all 11 story IDs, 3 Bugs, 25 Tasks, 50 Delivery Events, April 8–19 2030 dates, and task hours are consistent with the documented fictional scenario. Records contain no employee/assignee identities or direct employer/client/proprietary-project identifiers. This verifies the supplied records and their declared fictional provenance; it does not independently prove external ownership/provenance.

## Hygiene changes made

- `.gitignore`: added generated coverage and static-analysis cache patterns.
- `README.md`: removed inconsistent blank lines in the documentation list.
- `data/demo/sprint-08/README.md`: removed the unnecessary employer disclaimer reference and corrected objectively stale implementation status.
- `data/README.md`, `data/schema.md`: corrected implemented-service/calculation references.
- `docs/technical-decisions.md`: corrected stale placeholder-page and fixture-consumption statements.
- `docs/product-principles.md`: corrected the foundation-only status sentence.
- This audit report was added. No substantive document, screenshot, source file, or business record was removed.

Existing ignore rules correctly exclude node_modules, Next output, virtualenvs, Python/test caches, environment files, logs, OS files, and TypeScript build info. No generated artifact is tracked, and no unwanted cache/build file is eligible for publication. `next-env.d.ts` is a small standard generated framework declaration with relative imports; it contains no private information. Eleven intentional screenshots are retained. Local Markdown links resolve; no absolute personal-path replacements were necessary.

## README review

| Reader question | Assessment |
| --- | --- |
| What is ADI? | Clear opening purpose and product positioning. |
| What problem does it solve? | Delivery context and traceability are explained. |
| How does it differ from trackers? | Explicitly complementary; no exaggerated exclusivity claims. |
| What does v0.1 demonstrate? | All three implemented vertical slices are described near the top. |
| Architecture? | A directory tree and technologies exist; the end-to-end data flow is missing. |
| Run locally? | Frontend/backend commands and configuration exist below the opening screen. |
| Fictional data? | Mentioned in the directory tree and linked dataset docs; make it prominent earlier. |
| Status? | Feature-complete milestone is clear; Early Development is the broader project status. Explain that distinction if polishing. |

For a recruiter, the missing screenshots are the largest presentation gap. Engineering readers have meaningful code, boundaries, tests, and setup details. Product and Agile Delivery readers have useful principles and domain semantics, but could benefit from a compact three-view introduction and one causal example. A complete README rewrite was not performed.

## Documentation classification

- **Publicly useful:** product principles, milestones, all three intelligence-engine documents, all three UI documents, schema, scenario README, and Sprint 08 audit. They explain semantics, evidence, scope boundaries, and implementation choices.
- **Internal but safe:** technical decisions, per-slice verification histories, captured frontend API fixtures, and this audit. Historical test counts refer to earlier slices, not today's suite.
- **Candidate for cleanup:** repeated freeze paragraphs, historical “future/no implementation” language inside earlier decision sections, repeated Product Owner-resolution notes, and the original empty-dataset example. Retain substantive material pending approval; link current docs instead of expanding repetition.

The architecture is explained piecemeal. Minimum recommended addition: one diagram or short paragraph showing `Frozen demo JSON → pure domain engines → fixture-loading services / FastAPI demo routes → typed Next.js server clients → Sprint Intelligence UI`, naming Burndown, Delivery Flow, and Quality & Rework. This is documentation of existing architecture, not a proposal for new infrastructure.

## Screenshots

All eleven screenshots were visually reviewed across this work session and prior slice verification. They are legible and visually consistent, with fictional IDs and no browser chrome, private URLs, personal paths, employee names, or production data. PNG inspection found no text/EXIF metadata chunks. Total size is approximately 0.8 MiB.

Recommended README selections:

1. [Sprint Health desktop](screenshots/sprint-health-desktop.png): strongest complete view; scenario label, summary, and chart visible.
2. [Delivery Flow chart](screenshots/delivery-flow-desktop-chart.png): strongest workflow visualization; add a “fictional Sprint 08” caption because the crop omits the page summary label.
3. [Quality & Rework desktop](screenshots/quality-rework-desktop.png): summary and first-pass ratio with fictional-demo label.
4. Optional supporting detail: [mobile active rework](screenshots/quality-rework-mobile-active.png) or [Day 6 causal detail](screenshots/sprint-health-day6-mobile.png).

Other mobile/chart-detail captures remain useful for responsive evidence. Cropped captures generally need a fictional-data caption when used alone. No screenshots were created, altered, or deleted in this audit.

## Reproducibility and dependencies

- Node `>=24.0.0` is configured; observed Node 24.16.0 and npm 11.17.0.
- Python 3.14+ is documented; observed Python 3.14.6. There is no runtime version file or `requires-python` declaration.
- README provides `npm ci`, frontend start, virtualenv creation/activation, pip installation, backend start, the API default, and optional `ADI_API_BASE_URL` configuration.
- `package-lock.json` pins frontend resolution. Backend direct production/test requirements are separated and pinned.
- No obviously unused direct dependencies or test-only imports in production code were found. React DOM is part of the Next/React runtime even without a direct application import.
- Preserve ESLint 9.39.5: its Next React-plugin compatibility rationale is documented. No broad upgrades were attempted.
- `npm audit` reported **0 vulnerabilities** after the initial sandbox DNS failure was retried with network access. `pip check` reported **no broken requirements**; that is dependency consistency, not a Python vulnerability scan. A backend advisory scan remains unperformed.
- Full checks pass in the existing installed environment. A fresh-machine installation was not performed; do not treat this as proof of every clean-environment/platform combination.

## Validation evidence

The full suite was run once after the permitted hygiene changes:

| Check | Result |
| --- | --- |
| Backend pytest, warnings treated as errors | 88 passed: 34 Quality & Rework, 23 Delivery Flow, 30 Burndown, 1 health |
| Frozen fixture unittest | 21 passed |
| Frontend Vitest | 59 passed |
| ESLint | Passed |
| TypeScript / Next type generation | Passed |
| Production Next build | Passed |

Byte comparisons confirm all application files, test fixtures, and frozen scenario JSON remained unchanged. The only changes under `data/` are the three documentation files listed above. The existing digest tests passed without changing their expected values.

## Git and scope

Current branch is unborn `master`; zero tracked files, no commits or tags, no remote. The working tree is intentionally not clean: all project content remains untracked, including hygiene edits and this report. There is no authored commit history to review or rewrite. Local Codex refs point to trees, not commits; local object storage includes historical blobs. No Git configuration, ref, history, remote, or index changes were made.

Exactly three implemented vertical slices are present: Burndown, Delivery Flow, and Quality & Rework, each with dataset → domain → demo API → UI. Capacity Health, Impediments, Portfolio, Release Readiness, integrations, and AI recommendations are not implemented claims; they appear only as future work, boundaries, or product positioning. The optional future expected/ideal Burndown trajectory is also not presented as implemented.

## Metadata recommendation and deployment assessment

Suggested repository slug: `agile-delivery-intelligence`.

Suggested description: “Sprint delivery intelligence with traceable burndown, workflow composition, and QA/rework analysis using fictional demo data.”

Suggested topics: `agile`, `scrum`, `delivery-management`, `sprint-intelligence`, `fastapi`, `nextjs`, `typescript`, `python`, `portfolio`.

Recommend an initial private staging repository, then public visibility after licensing and final publication review. This is a recommendation only. npm's `private: true` prevents package publication; it does not define GitHub visibility.

The architecture is deployable but is not deployment-configured:

- **Frontend:** a Next-compatible Node runtime, install/build stage including development build tools, and the existing workspace start command; dynamic server fetching prevents a static-export-only deployment.
- **Backend:** a Python ASGI runtime with production requirements and a serving command. Include `data/demo/sprint-08` at the repository-relative location expected by the loaders; deploying only `apps/api` would omit the fixture. Bind host/port to the chosen runtime when later configured.
- **Configuration:** set server-only `ADI_API_BASE_URL` to the backend's reachable URL. Loopback defaults only work when the API shares the runtime host. No database, browser API credential, external integration, or new CORS dependency is needed for the current server-fetch arrangement.
- **Provider:** none is configured or selected. Runtime support, HTTPS, process supervision, and routing must be checked during an approved hosting task. No Docker or infrastructure was added.

No GitHub repository, remote, push, tag, release, deployment, license, or v0.2 functionality was created.
