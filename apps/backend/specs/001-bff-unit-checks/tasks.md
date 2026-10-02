---

description: "Task list for channel gateways and merge checks"
---

# Tasks: Channel Gateways and Merge Checks

**Input**: Design documents from `/specs/001-bff-unit-checks/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Required. The specification's deliverable is pytest behavior checks for the two gateways, plus the workflow that runs them. The constitution does not require a red-green cycle. Each story's tests must pass before that story's checkpoint.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Gateways: `apps/backend/bff-web/` and `apps/backend/bff-movil/`
- Workflow: `.github/workflows/backend-unit-tests.yml` at the git repository root (parent of `apps/`)
- Selector: `apps/backend/scripts/`
- Contracts: `specs/001-bff-unit-checks/contracts/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the two gateway packages without adding domain services

- [X] T001 Create `apps/backend/bff-web/pyproject.toml` requiring Python >=3.10, depending on FastAPI, Pydantic v2, and PyJWT, with `[tool.fastapi] entrypoint = "app.main:app"` and a `test` extra of pytest and httpx
- [X] T002 [P] Create `apps/backend/bff-movil/pyproject.toml` with the same Python, dependency, entrypoint, and `test` extra rules as T001

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Package layout and token checks that every screen depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create empty `apps/backend/bff-web/app/__init__.py` and `apps/backend/bff-web/app/routers/__init__.py`
- [X] T004 [P] Create empty `apps/backend/bff-movil/app/__init__.py` and `apps/backend/bff-movil/app/routers/__init__.py`
- [X] T005 Implement mock HS256 tokens in `apps/backend/bff-web/app/dependencies.py` using `SOLVENTA_TOKEN_SECRET`, claims `sub`, `rol`, and `exp`, `expiraEn` of 900 seconds, any non-empty `correo` and `contrasena`, and `rol` limited to `cliente`, `asesor`, or `operador`
- [X] T006 [P] Implement mock HS256 tokens in `apps/backend/bff-movil/app/dependencies.py` with the same secret and `expiraEn` of 900 seconds, no `rol` field on sign-in, always `rol` `cliente`, and rejection of `asesor` and `operador` tokens
- [X] T007 Create `apps/backend/bff-web/app/main.py` with a `FastAPI` instance and no path operations yet
- [X] T008 [P] Create `apps/backend/bff-movil/app/main.py` with a `FastAPI` instance and no path operations yet

**Checkpoint**: Both apps import as `app.main:app`. User story work can begin.

---

## Phase 3: User Story 1 - Server decides access for web and mobile (Priority: P1) 🎯 MVP

**Goal**: Both gateways answer the Contratos BFF bodies with mocks, and the web desk role limits which screens accept the token

**Independent Test**: From each gateway directory, install the `test` extra and run `pytest tests -m "not integration and not contract"`. The quickstart scenarios in `specs/001-bff-unit-checks/quickstart.md` pass without a domain service.

### Tests for User Story 1

- [X] T009 [P] [US1] Add TestClient setup that sets `SOLVENTA_TOKEN_SECRET` in `apps/backend/bff-web/tests/conftest.py`
- [X] T010 [P] [US1] Add TestClient setup that sets `SOLVENTA_TOKEN_SECRET` in `apps/backend/bff-movil/tests/conftest.py`
- [X] T011 [P] [US1] Cover web sign-in, refresh, logout, and a rejected `rol` outside `cliente`, `asesor`, and `operador` in `apps/backend/bff-web/tests/test_sesion.py`
- [X] T012 [P] [US1] Cover web registration fields `nombre`, `apellidos`, `documento`, `correo`, and `habeasData` in `apps/backend/bff-web/tests/test_registro.py`
- [X] T013 [P] [US1] Cover customer quote, re-read, issue, wallet, detail, payment trace, mortgage, and home in `apps/backend/bff-web/tests/test_cliente.py`, including `COT-RECHAZADA` refusal motivo "Valor del equipo fuera de rango", numeric `monto`/`prima` with `moneda` and no locale, and `consentimientoPerfil` false returning `degradada` true with prima 50000 COP
- [X] T014 [P] [US1] Cover advisor portfolio, client file create without `clienteId`, deactivate `estado` `inactivo`, and assisted sale, and assert 403 for every other protected web screen, in `apps/backend/bff-web/tests/test_asesor.py`
- [X] T015 [P] [US1] Cover the operator queue, `rechazar` without `motivo` as 400, `cancelar` without `motivo` as 400, `cancelar` with `motivo` setting `estado` `cancelada`, and assistance status absent from the queue, in `apps/backend/bff-web/tests/test_operador.py`
- [X] T016 [P] [US1] Cover mobile sign-in without `rol`, ignored `rol` on a later call, and 403 for advisor and operator tokens in `apps/backend/bff-movil/tests/test_sesion.py`
- [X] T017 [P] [US1] Cover `pruebaDeVida` `ok` and `no`, refusal of any other value, no selfie field, and `{ "habeasData": false }` in `apps/backend/bff-movil/tests/test_registro.py`
- [X] T018 [P] [US1] Cover mobile quote, wallet, claim notice with `geo` null and `estado` `recibido`, automatic payment, mortgage, in-app notices, home, push token, one push payload, provider list, and assistance request in `apps/backend/bff-movil/tests/test_cliente.py`

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement `POST /sesion/ingreso`, `POST /sesion/refresh`, and `POST /sesion/salida` in `apps/backend/bff-web/app/routers/sesion.py` with prefix `/sesion` (no trailing slash) and logout allowed for any valid web role
- [X] T020 [P] [US1] Implement `POST /registro` in `apps/backend/bff-web/app/routers/registro.py` with prefix `/registro` and no auth dependency
- [X] T021 [P] [US1] Implement customer routes from `specs/001-bff-unit-checks/contracts/bff-web.md` in `apps/backend/bff-web/app/routers/cliente.py` with prefix `/cliente` and dependency role `cliente` only; refuse a body that includes `clienteId` on the quote
- [X] T022 [P] [US1] Implement advisor routes from `specs/001-bff-unit-checks/contracts/bff-web.md` in `apps/backend/bff-web/app/routers/asesor.py` with prefix `/asesor` and dependency role `asesor` only
- [X] T023 [P] [US1] Implement operator routes from `specs/001-bff-unit-checks/contracts/bff-web.md` in `apps/backend/bff-web/app/routers/operador.py` with prefix `/operador` and dependency role `operador` only; `verbo` is `renovar`, `modificar`, or `cancelar`; `decision` is `aprobar` or `rechazar`
- [X] T024 [US1] Import `sesion`, `registro`, `cliente`, `asesor`, and `operador` as modules and call `include_router` in `apps/backend/bff-web/app/main.py` (do not import bare `router` names)
- [X] T025 [P] [US1] Implement `POST /sesion/ingreso`, `POST /sesion/refresh`, and `POST /sesion/salida` in `apps/backend/bff-movil/app/routers/sesion.py` with prefix `/sesion`; sign-in has no `rol` field and the token role is `cliente`
- [X] T026 [P] [US1] Implement `POST /registro` and `POST /registro/consentimiento` in `apps/backend/bff-movil/app/routers/registro.py` with prefix `/registro`; `pruebaDeVida` is only `ok` or `no`
- [X] T027 [P] [US1] Implement customer routes from `specs/001-bff-unit-checks/contracts/bff-movil.md` in `apps/backend/bff-movil/app/routers/cliente.py` with prefix `/cliente`, customer token only, and any request `rol` ignored; duplicate the automatic-payment fields locally (`siniestroId`, `poliza`, `umbral`, numeric `monto`, `moneda`, `estado` `pagado`) and do not import `bff-web`
- [X] T028 [US1] Import `sesion`, `registro`, and `cliente` as modules and call `include_router` in `apps/backend/bff-movil/app/main.py`

**Checkpoint**: User Story 1 passes `pytest` in both gateway directories. No domain directory was modified.

---

## Phase 4: User Story 2 - A gateway change is checked before merge (Priority: P2)

**Goal**: A pull request into `develop`, `main`, `release/*`, or `hotfix/*`, and a push to `feature/*`, runs pytest for each changed gateway. A push to `develop`, `main`, `release/*`, or `hotfix/*` runs both gateways even when neither directory changed

**Independent Test**: Run the selector tests. A changed-path set of only `apps/backend/bff-web` on a pull request into `develop` selects `bff-web`. A push to `main` with no gateway paths selects both `bff-web` and `bff-movil`. A push to `release/*` or `hotfix/*` does the same. A push to `feature/*` that changes only `bff-web` selects `bff-web`. A pull request into a branch outside this set selects nothing.

### Tests for User Story 2

- [X] T029 [P] [US2] Add selector tests for pull-request path filtering into `develop`, `main`, `release/*`, and `hotfix/*`, the always-both push rule for those lines, and the `feature/*` path filter in `apps/backend/scripts/tests/test_select_required.py`

### Implementation for User Story 2

- [X] T030 [P] [US2] Implement required-gateway selection in `apps/backend/scripts/select_services.py` for pull requests into `develop`, `main`, `release/*`, and `hotfix/*`, pushes to those lines, and path-filtered pushes to `feature/*`
- [X] T031 [US2] Add `.github/workflows/backend-unit-tests.yml` at the git root that triggers on `pull_request` into `develop`, `main`, `release/**`, and `hotfix/**`, and on `push` to `develop`, `main`, `feature/**`, `release/**`, and `hotfix/**`, for paths `apps/backend/**`, uses Python 3.10 or newer, installs the selected gateway `test` extra, imports `app.main:app`, fails if `tests/` contains `sleep(`, runs `pytest` excluding markers `integration` and `contract`, fails when zero tests are collected, uploads a JUnit report, and uploads coverage without a percentage gate

**Checkpoint**: The workflow runs the two gateways in process and does not start a database, cache, bus, or container.

---

## Phase 5: User Story 3 - Other domains are checked only when they already have checks (Priority: P3)

**Goal**: An existing backend domain runs only when the change touches it and it already has a test file; otherwise the check stays green and states why

**Independent Test**: Selector cases for a domain with no `tests/` file, a domain with tests but no `pyproject.toml`, a domain with tests but no `app/main.py`, and a domain with tests and a package. Only the last is selected. A skip reason is non-empty for the others.

### Tests for User Story 3

- [X] T032 [US3] Add optional-domain cases to `apps/backend/scripts/tests/test_select_optional.py` for missing tests, missing `pyproject.toml`, missing `app/main.py`, and a later directory that uses the same markers

### Implementation for User Story 3

- [X] T033 [US3] Extend `apps/backend/scripts/select_services.py` so optional directories under `apps/backend/` (including `api-socios` and every `ms-*` folder) are selected only when changed and `tests/` contains at least one test file, and so a missing package or `app/main.py` returns a skip reason instead of a failure
- [X] T034 [US3] Extend `.github/workflows/backend-unit-tests.yml` so a skipped optional domain writes its reason to the job summary and does not fail the required check, while a selected optional domain that fails `pytest` fails the check

**Checkpoint**: A change that only touches a domain with no tests does not fail the workflow. A domain that later gains tests is included without editing the workflow.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Leave the gateways describable and confirm the quickstart

- [X] T035 [P] Replace the pending-implementation line in `apps/backend/bff-web/README.md` with the contract path `specs/001-bff-unit-checks/contracts/bff-web.md`
- [X] T036 [P] Replace the pending-implementation line in `apps/backend/bff-movil/README.md` with the contract path `specs/001-bff-unit-checks/contracts/bff-movil.md`
- [X] T037 Run the gateway commands in `specs/001-bff-unit-checks/quickstart.md` and the selector tests in `apps/backend/scripts/tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup. Blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on US2 or US3
- **User Story 2 (Phase 4)**: Depends on Foundational. Its live workflow run is meaningful after US1 tests exist. The selector tests do not import the gateways
- **User Story 3 (Phase 5)**: Depends on the workflow and selector from US2 because it extends those same files
- **Polish (Phase 6)**: Depends on US1, US2, and US3

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. Independent of the workflow
- **User Story 2 (P2)**: Starts after Foundational. Does not require US3
- **User Story 3 (P3)**: Starts after US2. Does not change gateway routers

### Within Each User Story

- Story tests and story routers that touch different files can proceed together
- `include_router` in `app/main.py` waits until that gateway's routers exist
- US3 edits `select_services.py` and the workflow after US2 has created them
- A story checkpoint requires its tests to pass. A failing-first cycle is not required

### Parallel Opportunities

- T001 and T002
- T003 and T004; T005 and T006; T007 and T008
- T009 through T018
- T019 through T023; T025 through T027
- T029 and T030
- T035 and T036

---

## Parallel Example: User Story 1

```bash
# Web and mobile test modules, different files:
Task: "T011 apps/backend/bff-web/tests/test_sesion.py"
Task: "T016 apps/backend/bff-movil/tests/test_sesion.py"

# Web routers, different files:
Task: "T019 apps/backend/bff-web/app/routers/sesion.py"
Task: "T021 apps/backend/bff-web/app/routers/cliente.py"
Task: "T022 apps/backend/bff-web/app/routers/asesor.py"
Task: "T023 apps/backend/bff-web/app/routers/operador.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete Phase 3
3. Stop and run `pytest` in `apps/backend/bff-web` and `apps/backend/bff-movil`

### Incremental Delivery

1. Setup and foundational token dependencies
2. User Story 1 gateways and their pytest suites
3. User Story 2 required workflow
4. User Story 3 optional-domain selection
5. Polish readmes and the quickstart run

### Parallel Team Strategy

1. One person scaffolds both packages (Phase 1 and Phase 2)
2. Then one person can take `bff-web` routers and tests while another takes `bff-movil`
3. The workflow (US2, then US3) starts after the gateway test trees exist

---

## Notes

- [P] tasks use different files and do not depend on an unfinished edit of the same file
- Do not add code under `api-socios` or any `ms-*` directory
- Do not add Pact, k6, Toxiproxy, deploy, SAST, or a coverage percentage gate
- Prefixes must not end with `/`. Do not import several bare `router` names into `main.py`
- Commit after each task or logical group
