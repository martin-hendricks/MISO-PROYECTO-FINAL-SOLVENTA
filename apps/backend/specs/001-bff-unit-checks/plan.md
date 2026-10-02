# Implementation Plan: Channel Gateways and Merge Checks

**Branch**: `001-bff-unit-checks` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-bff-unit-checks/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Add the web and mobile channel gateways as two FastAPI packages that return the Contratos BFF bodies from in-process fixtures, including every alternate body that page already writes. Protect screens by the role carried in a mock token. Add a GitHub Actions workflow at the git root that follows Gitflow. A pull request into `develop`, `main`, `release/*`, or `hotfix/*`, and a push to `feature/*`, unit-tests a gateway only when that directory changed. A push to `develop`, `main`, `release/*`, or `hotfix/*` always unit-tests both gateways. Any other backend domain is unit-tested only when it already has tests. `support/` is not used.

## Technical Context

**Language/Version**: Python 3.10 or newer

**Primary Dependencies**: FastAPI, Pydantic v2, PyJWT, pytest, HTTPX (TestClient)

**Storage**: N/A. Fixtures are in memory. No database, cache, or message bus.

**Testing**: pytest with FastAPI TestClient. Markers `integration` and `contract` are excluded. No `sleep()`.

**Target Platform**: GitHub Actions runner for checks. The same package is what a later container would start. This feature does not build an image.

**Project Type**: Two web services (channel gateways) plus one workflow

**Performance Goals**: None for this feature. Latency budgets are not claimed and are not measured here.

**Constraints**: Mock answers only. No domain service, partner API, cloud client, or fixed wait. Money is a number plus a currency code. Role mismatches return 403. A skipped domain must not fail the required check. The workflow triggers for pull requests into `develop`, `main`, `release/*`, or `hotfix/*`, and for pushes to `develop`, `main`, `feature/*`, `release/*`, or `hotfix/*`.

**Scale/Scope**: Two gateways and the contracts listed in [contracts/bff-web.md](contracts/bff-web.md) and [contracts/bff-movil.md](contracts/bff-movil.md). Existing domain directories stay unimplemented.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Modular FastAPI services | Pass. Each gateway is its own package: `app/main.py` only includes routers, dependencies live in `app/dependencies.py`, prefixes do not end with `/`. | Pass. Contracts assign one router per role, included from `main.py`. |
| II. One domain core behind the edge | Pass with the justification below. Gateways do not implement rating, underwriting, claims, or payments. They return published channel bodies. | Pass. No gateway imports another service. The shared payment body is duplicated, not imported. |
| III. Python unit tests per development | Pass. Each gateway ships pytest tests. A failing, empty, or sleeping suite blocks merge. | Pass. Quickstart and the workflow run `pytest` in process, with dependencies overridden by fixtures. |
| IV. Contracts at the boundary | Pass. This change does not call a domain or partner service, so consumer-driven contract tests are not required. Channel bodies are recorded under `contracts/`. | Pass. The workflow excludes the `contract` marker. Pact stays out of scope. |
| V. Latency, safety, idempotency | Pass. This feature does not sit on the Open Finance path and must not pause. A green unit run is not evidence of a latency budget. | Pass. The only slow outcome is `degradada: true` with the fallback premium. |
| Integration branch | Pass. Gitflow matches the constitution: `develop` integrates features, `main` records releases, and `feature/*`, `release/*`, and `hotfix/*` follow the stated parents and merge targets. | Pass. Workflow, quickstart, and tasks name those branches. `support/` is not used. |

## Project Structure

### Documentation (this feature)

```text
specs/001-bff-unit-checks/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── bff-web.md
│   └── bff-movil.md
└── tasks.md             # /speckit-tasks, not this command
```

### Source Code (repository root)

```text
apps/backend/bff-web/
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── dependencies.py
│   └── routers/
│       ├── __init__.py
│       ├── sesion.py
│       ├── registro.py
│       ├── cliente.py
│       ├── asesor.py
│       └── operador.py
└── tests/

apps/backend/bff-movil/
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── dependencies.py
│   └── routers/
│       ├── __init__.py
│       ├── sesion.py
│       ├── registro.py
│       └── cliente.py
└── tests/

.github/workflows/backend-unit-tests.yml
```

The workflow path is the git repository root, the parent of `apps/`. GitHub does not read a workflow nested under `apps/backend`.

**Structure Decision**: Two existing service directories, each a FastAPI bigger application. Role groups are routers. `main.py` imports those modules and calls `include_router`. Optional domains (`api-socios`, `ms-cotizacion`, `ms-consentimiento`, `ms-identidad`, `ms-pagos`, `ms-parametrico`, `ms-perfilamiento`, `ms-polizas`, `ms-siniestros`, `ms-suscripcion`) are discovered by the workflow and are not given new code. A later directory that has the same markers is picked up without editing the workflow.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Each gateway mints the mock token instead of `ms-identidad` | Sign-in must return a token this feature can validate, and FR-018 forbids implementing `ms-identidad`. Issuance sits in one dependency so routers do not change when the real issuer arrives. | Calling `ms-identidad` requires a service this branch must not create. An unsigned token would let the client choose the role. |
