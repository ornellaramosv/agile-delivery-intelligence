# Manual Vercel deployment — ADI v0.1.0

Two separate projects use `ornellaramosv/agile-delivery-intelligence`, branch `main`.
Keep GitHub Private. No CLI is required. Repository configuration is prepared; a successful cloud deployment is not yet claimed.

## Before importing

1. Select the intended team. Confirm **Team Settings → Data Preferences → Opt-Out** for model training before repository authorization.
2. If GitHub access is requested, select **Only select repositories → agile-delivery-intelligence**. Do not authorize all repositories.
3. Use **Add New → Project** for a fresh import. Failed projects may retain old overrides; do not treat them as authoritative.
4. Vercel may detect three directories. Import only the root in Phase A and only `apps/web` in Phase B.

## Phase A — Backend

| Vercel field | Exact choice |
|---|---|
| Repository / branch | `ornellaramosv/agile-delivery-intelligence` / `main` |
| Project Name | `adi-api` |
| Framework / Application Preset | **FastAPI** |
| Root Directory | `.` (repository root, displayed as the repository name in the directory picker) |
| Install Command | `uv pip install -r requirements.txt`, supplied by root `vercel.json` |
| Build Command | Automatic FastAPI default (`null` in root `vercel.json`); Override **off** |
| Output Directory | Default; no override |
| Environment Variables | None |
| Include source files outside Root Directory in the Build Step | Not required because the entire repository is the root |

Leave command/output **Override** switches off. The committed JSON determines the commands. If the UI shows `npm install --prefix=../..` or `npm run build`, confirm the root and preset and use a fresh import rather than copying old overrides. The JSON overrides project settings at build time.

Python **3.14** comes from `.python-version`. Root `index.py` exports the existing app. Vercel invokes ASGI; do not enter a Uvicorn start command, output folder, or `/api` rewrite.

Click **Deploy**. Logs must show Python installation, not a Next.js build. After **Ready**, copy the assigned **Production domain**. Do not guess it from the project name. Confirm this domain is accessible without login; preview deployments may remain protected.

### Verify backend before Phase B

Open these paths on the assigned HTTPS origin in a private/signed-out browser window. Use the Network panel to confirm HTTP 200 and JSON, not a login page.

| Path | Expected values |
|---|---|
| `/health` | `status: ok`, `service: adi-api` |
| `/demo/sprint-08/burndown` | Day 10 `original_baseline: 10`, `current_remaining_work: 5` |
| `/demo/sprint-08/delivery-flow` | Day 10 `total_active_scope: 11`, `closed_stories: 7`, `open_stories: 4` |
| `/demo/sprint-08/quality-rework` | Eligible 7, passed 4, failed 3, rate about 0.5714286; cycles 3, active 1; tasks 7, estimated 45, completed 45, remaining 8 |

Record first-request and immediate-repeat timing. This is not proof that a request was a cold start. The frontend timeout is 10 seconds. Health alone does not verify fixture loading: all three demo routes must pass.

## Phase B — Frontend

Import the same repository into a second fresh project after backend verification.

| Vercel field | Exact choice |
|---|---|
| Repository / branch | `ornellaramosv/agile-delivery-intelligence` / `main` |
| Project Name | `adi-web` |
| Framework / Application Preset | **Next.js** |
| Root Directory | `apps/web` |
| Install Command | `cd ../.. && npm ci`, supplied by `apps/web/vercel.json` |
| Build Command | `npm run build`, supplied by `apps/web/vercel.json` |
| Output Directory | Default Next.js output; no override |
| Node.js Version | **24.x**, also constrained by the frontend manifest |
| Include source files outside Root Directory in the Build Step | **Enabled** |
| Environment Variables | `ADI_API_BASE_URL` = verified backend HTTPS origin, scoped to **Production** |

Leave command/output Override switches off. Installation runs from repository root using the npm workspace lockfile; building runs in `apps/web`. Each project reads the JSON in its selected root.

Use an origin such as `https://YOUR-BACKEND-DOMAIN.vercel.app`, replacing the placeholder with the real Phase A domain. Do not append an endpoint, path prefix, query, credentials, or fragment. A trailing slash is accepted. Preview needs its own environment scope if it should load demo data.

Click **Deploy**. Next.js uses dynamic server rendering, not static export. The provider manages the server. A conventional local production server uses `npm run start --workspace @adi/web` from repository root after building.

### Verify frontend

- Open `/`, `/sprint-health`, `/delivery-flow`, and `/quality-rework` without login.
- Verify navigation, desktop and mobile layouts, and no unexpected browser console errors.
- All views must display data without an unavailable state. Compare values with Phase A.
- Confirm the fictional-data disclosure; original baseline stays 10 although active scope reaches 11.
- Do not mark ADI Live until these checks pass. Do not create a tag/release or change GitHub visibility as part of these steps.

## Technical decisions and validation boundary

- Root npm metadata plus Python manifests at root and `apps/api` allow competing detection candidates. The observed `npm install --prefix=../..` is consistent with parent-workspace npm detection for a nested root. Exact failed-project history is unknown without provider logs; retained UI settings may also contribute.
- Backend JSON explicitly selects FastAPI, Python installation, and the automatic FastAPI build behavior (`buildCommand: null`). The Python builder provides `uv` and a build virtual environment. The custom command installs requirements there; the builder vendors runtime dependencies. Root `requirements.txt` directly lists the runtime pins so Vercel can analyze it without following includes. `apps/api/requirements.txt` delegates to that root file for local installation.
- Uvicorn remains for local/conventional ASGI hosting; Vercel does not need it as a process supervisor. pytest and httpx2 remain test-only dependencies in `requirements-dev.txt`.
- No unique requirement for Python 3.14 was identified, but it is the validated project baseline and a supported Vercel runtime. Downgrading would not solve the npm ambiguity, so retain it.
- Python bundles project files by default. Backend `excludeFiles` removes frontend code/dependencies, docs, tests and caches while retaining the original `apps/api/app` and `data/demo/sprint-08` hierarchy. No fixture duplication or include override is necessary.
- Fixture paths derive from `__file__`, independent of working directory and personal paths. An isolated-copy test verifies the root adapter and all four routes from an unrelated working directory against direct engine output.
- Data fetching remains server-side. No CORS middleware is needed. Production requires `ADI_API_BASE_URL`; invalid/missing configuration fails before fetching. Existing unavailable-page presentation is retained. Development defaults to localhost.
- The backend needs no application secrets. API origin is non-secret configuration. Hosting credentials and GitHub permissions are separate administrative concerns.
- No Docker, Procfile, database, persistent storage, health changes, or routing layer is needed. `.vercel/` is ignored.
- Clean local installation, tests and builds do not prove the provider's actual bundle or domain configuration. No authenticated Vercel CLI build is performed. Cloud verification remains required during manual deployment.
- Check current Hobby eligibility and quotas in the selected account. Two projects consume account resources; cold starts and exhausted build/compute/bandwidth limits can affect availability.

## Troubleshooting

| Symptom | Action |
|---|---|
| Backend runs npm/Next.js | Verify root `.`, FastAPI preset, latest `main`, root JSON, and fresh import. Do not copy old UI overrides. |
| Python installation error | Confirm `uv pip install -r requirements.txt` and both requirements files. Save the first error; do not upgrade dependencies blindly. |
| `ModuleNotFoundError: app` | Confirm root `index.py` and packaged `apps/api/app`; root must not be `apps/api`. |
| Fixture missing / demo HTTP 500 | Confirm original `data/demo/sprint-08` is bundled. Report the exact missing path before moving or copying frozen data. |
| Backend `/` gives 404 | Expected: use `/health`; the backend has no home page. |
| Documented routes give 404 | Check FastAPI and root entrypoint. Do not introduce an `/api` prefix. |
| Login HTML / HTTP 401 | Use the public Production domain and review Production Deployment Protection. Do not add bypass tokens to URLs. |
| Frontend lockfile missing | Enable outside-root source access and retain the committed install command. |
| Frontend unavailable | Verify Production API origin, backend public access, all demo routes, and latency. Redeploy after environment changes. |
| First request fails; repeat succeeds | Compare measured latency with 10-second timeout before changing application behavior. |
| Provider behavior differs | Preserve logs and stop; do not guess settings or alter business logic. |

## References

- [FastAPI entrypoints and function configuration](https://vercel.com/docs/frameworks/backend/fastapi)
- [Python versions and bundling](https://vercel.com/docs/functions/runtimes/python)
- [Configuration overrides](https://vercel.com/docs/project-configuration/vercel-json)
- [Python builder source](https://github.com/vercel/vercel/blob/main/packages/python/src/index.ts)

## Local validation evidence — deployment hardening

- Clean npm workspace install in a temporary checkout: passed; no dependency versions changed.
- Clean Python runtime-only installation using the configured uv command: passed; pip check passed. Development dependencies installed separately for testing.
- Backend: 91 tests passed, including isolated adapter/fixture/route test. Dataset: 21 passed. Frontend: 69 passed. Lint, TypeScript and production build passed.
- Local Uvicorn HTTP checks: health and all three demo endpoints passed; demo payloads exactly matched existing frontend reference fixtures. Local production Next.js served all three views with API-fetched sprint metadata. Temporary servers were stopped.
- Vercel JSON field validation passed against the public schema. Its mixed-draft meta-schema prevented strict validation of the provider schema itself; meta-schema validation was disabled for field checks. Exclusion-glob checks retained required app/data files and excluded frontend/tests. Actual cloud bundling remains unverified.
- npm reported the existing ESLint 9 deprecation and two dependency install-script policy warnings, but installation and all checks passed. Preserve the documented ESLint compatibility choice; no broad upgrade was performed.
- Frozen fixture, backend domain/routes/services and visual components remained byte-for-byte unchanged. No provider authentication, project creation or deployment occurred.

### Correction: unmatched `functions.index.py` pattern

The previous `buildCommand: ""` reproduced the exact error about `index.py` not matching a function inside `api`. Vercel's filesystem detector interprets an empty build command (or output directory) as a static deployment and skips the Python framework builder. The adapter itself is recognized correctly.

The correction is `buildCommand: null`, which retains FastAPI's default behavior without running the root npm build. Leave Build Command and Output Directory Override switches **off**; do not enter an empty custom command or output directory. Keep the root, adapter and `functions.index.py` exclusion configuration unchanged.

Reproduced locally with the published `@vercel/fs-detectors` library: the previous configuration returns `unused_function`; the corrected configuration selects `@vercel/python` with no detection errors. This is a build-plan check, not a cloud deployment.

### Correction: root requirements include parsing

Vercel CLI 61.1.0 failed before installation while parsing root `-r apps/api/requirements.txt`. Root `requirements.txt` now directly contains the unchanged FastAPI and Uvicorn pins. The local API requirements file includes the root manifest instead. This keeps one canonical runtime dependency list and preserves local/development install commands. No package versions changed. Retry with the commit containing this correction; Vercel UI settings remain unchanged.
