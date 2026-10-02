<!--
Sync Impact Report
- Version change: unratified template → 1.0.0
- Modified principles:
  - [PRINCIPLE_1_NAME] → I. Modular FastAPI Services
  - [PRINCIPLE_2_NAME] → II. One Domain Core Behind the Edge
  - [PRINCIPLE_3_NAME] → III. Python Unit Tests per Development (NON-NEGOTIABLE)
  - [PRINCIPLE_4_NAME] → IV. Contracts and Integration at the Boundary
  - [PRINCIPLE_5_NAME] → V. Measurable Latency, Safety, and Idempotency
- Added sections:
  - Architectural Constraints
  - Development Workflow and Quality Gates
- Removed sections: none (placeholder headings were replaced in place)
- Follow-up TODOs: none
- Sources: FastAPI Bigger Applications; Solventa wiki (team agreements);
  Estrategia de pruebas v3
-->

# Solventa Backend Constitution

## Core Principles

### I. Modular FastAPI Services

Each deployable backend service MUST be a Python package structured as a
FastAPI bigger application, not a single-file app.

- `app/main.py` creates the `FastAPI` instance, includes routers, and may
  declare only global dependencies. Path operations for a capability MUST
  live on an `APIRouter` in `app/routers/` (or `app/internal/` when the
  router is shared and must stay unmodified).
- Shared request dependencies MUST live in `app/dependencies.py` and be
  imported with package-relative imports.
- A router that shares prefix, tags, responses, or dependencies MUST declare
  them once on the `APIRouter` (or on `include_router`), not copied onto
  every path operation. A prefix MUST NOT end with `/`.
- `app/main.py` MUST import router modules (`users.router`) and MUST NOT
  import several bare `router` names into the same namespace.
- `pyproject.toml` MUST set `[tool.fastapi] entrypoint = "app.main:app"`.
- After a router is included, routes MUST be added only through path
  operation decorators or `include_router`. Code MUST NOT mutate
  `router.routes` directly.

Rationale: FastAPI keeps included routers live for routing and OpenAPI.
Colliding imports and a monolithic `main.py` hide boundaries and break docs.

### II. One Domain Core Behind the Edge

Business capabilities MUST be implemented once in the Python domain services.
Web, mobile, and partner channels MUST reach that core only through the edge.

- Domain services: `ms-cotizacion`, `ms-catalogo`, `ms-suscripcion`,
  `ms-perfilamiento`, `ms-polizas`, `ms-consentimiento`, `ms-socios`,
  `ms-identidad`, `ms-siniestros`, `ms-parametrico`, `ms-pagos`.
- Edge services: `bff-web`, `bff-movil`, and `api-socios`. They MUST expose
  channel-specific, versioned contracts. They MUST NOT duplicate rating,
  underwriting, policy, claims, or payment rules.
- `ms-identidad` MUST issue JWTs. The BFF or partner API that receives the
  call MUST validate the token and enforce role or scope. A channel change
  MUST NOT require redeploying the issuer.
- The backend MUST return amounts, currency, and locale as data. Formatting
  of text, dates, and currency MUST stay in the channel.
- External systems (Open Finance, Open Data, KYC, payments, signature,
  telemetry, reinsurance) MUST be reached through adapters. Domain code
  MUST NOT call those providers directly.

Rationale: the test strategy treats web and mobile as channels over one
core. Duplicating rules per channel makes verification and contracts diverge.

### III. Python Unit Tests per Development (NON-NEGOTIABLE)

Every backend development MUST include pytest unit tests that pass before
the work is done. Strict test-first (red-green-refactor) is NOT required.
Continuous testing is required: a story is not done without its unit tests.

- Tests MUST cover the statements and branches of the domain rules and
  calculations changed by that development (rating, underwriting, consent,
  policy state, claims, payment idempotency, JWT issuance).
- HTTP behavior of a router MUST be tested with FastAPI `TestClient` (or
  the async equivalent) against the service app, with dependencies overridden.
- Tests MUST use doubles for Open Finance, Open Data, KYC, and payments.
  They MUST NOT call real providers, a cloud environment, or a channel UI.
- Tests MUST NOT use `sleep()` or other static waits.
- A failing unit test MUST block merge. Known failing tests MUST NOT be
  left unresolved in CI.

Rationale: the team is four engineers with no separate QA group. The test
strategy makes unit tests of the shared Python core non-negotiable and
forbids timing-based or UI-coupled checks at this level.

### IV. Contracts and Integration at the Boundary

A change that crosses a service, edge, or external adapter MUST prove the
boundary, not only the unit.

- Integration tests MUST run with pytest and doubles of Open Finance, Open
  Data, KYC, and the payment gateway.
- A change to a contract consumed by `bff-web`, `bff-movil`, or `api-socios`
  MUST include consumer-driven contract tests (Pact). Existing consumers
  MUST keep working. A new major version MUST coexist with the previous one
  so clients are not force-upgraded together.
- The same router MAY be included more than once with different prefixes
  (for example `/api/v1` and `/api/latest`) when two versions must be served
  from one process.
- Critical journeys that this backend owns (embedded quote, subscribe and
  issue, assisted claim, parametric claim, mortgage life profiling, policy
  lifecycle) MUST have at least one automated scenario through the applicable
  edge when that journey's backend work is accepted.

Rationale: backwards compatibility (PI-01) and a single core are acceptance
criteria. Unit tests alone cannot show that a BFF and a domain service still
agree.

### V. Measurable Latency, Safety, and Idempotency

Design choices that sit on a critical path MUST protect the published budgets.
Evidence comes from the architecture experiments; every feature PR does not
re-run the full load suite.

- Embedded quote: Open Finance MUST be an opportunistic cache update with a
  fallback value, not a blocking call on the quote path. Per-dependency budget
  is 120 ms, with a hard timeout of 700 ms. Service-side targets that stand
  in for the end-to-end budget are p95 ≤ 225 ms and p99 ≤ 475 ms.
- Profiling fan-out to Open Finance and Open Data MUST be parallel.
  End-to-end targets are p95 ≤ 400 ms and p99 ≤ 800 ms.
- Accept-to-issued-policy MUST stay within p95 ≤ 1.5 s (nominal) and
  p99 ≤ 3 s (peak). Signature and notification MUST leave the synchronous
  path through the event bus.
- Claim-status reads that must meet p95 ≤ 150 ms MUST use the claims read
  model (`siniestros_r`, and cache only if the projection alone misses the
  budget). Write and read schemas MUST stay separate.
- Payment and parametric-event application MUST be idempotent: a retried
  command MUST NOT disburse or record a duplicate.
- Consent MUST be present before a call leaves to Open Finance. Revocation
  MUST be published as an event and MUST remove that data from later reads.
- Partner traffic MUST be isolated by quota. An abusive partner MUST receive
  429 or 403 and MUST NOT consume the latency budget of other tenants.

Rationale: these are the architecture requirements the test strategy uses as
oracles (HA-01 through HA-13 and the related security and modifiability
stories). Shipping a simpler design that misses the budget is a failed
experiment, not an implicit waiver.

## Architectural Constraints

Technology and structure are mandatory for this backend.

- Runtime: Python 3.10 or newer and FastAPI. Each service has its own
  `pyproject.toml` and application package. Services MUST NOT import each
  other's internals; they communicate by HTTP or by the event bus.
- Inside each service the package layout MUST be:

```
<service>/
├── pyproject.toml          # [tool.fastapi] entrypoint = "app.main:app"
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app and include_router only
│   ├── dependencies.py
│   └── routers/
│       ├── __init__.py
│       └── <capability>.py
└── tests/                  # pytest, one area per development
```

- Persistence: each service owns its schema. Transactional state uses
  PostgreSQL. Shared cache uses Redis (`CacheOF`, `CacheOD`, and the claims
  read cache when justified). Asynchronous facts use the event bus.
  Rating rules MUST be loadable without redeploying unrelated services.
- Deployment target is public cloud only (AWS: VPC, EKS multi-AZ, RDS
  PostgreSQL, ElastiCache Redis, MSK or an equivalent bus, WAF, KMS).
  Backend runtime MUST NOT depend on on-premises infrastructure.
- Load, chaos, and fault-injection runs (k6, Toxiproxy) MUST use the isolated
  experiment environment or local Docker Compose. They MUST NOT run against
  the minimal shared deploy or against real customer traffic.
- Regulatory certification, external penetration tests, a real payment
  acquirer, and multi-region failover are out of scope until a later
  constitution amendment. Stubs and adapters MUST still implement the
  expected contract and failure modes.

## Development Workflow and Quality Gates

Team agreements on the Solventa wiki govern how backend work is integrated.

- Branches follow feature branching from `develop`. New work starts from
  `develop` and merges back only through a pull request.
- A pull request MUST be approved by at least one other teammate before merge.
- Definition of Ready: the item is a user story or task on the GitHub Project
  board, prioritized, clear, and carrying acceptance criteria. It MUST NOT
  be pulled otherwise.
- Definition of Done: peer review approved, pytest unit tests for that
  development passing, and documentation updated when behavior or contracts
  change. Demo acceptance is what closes the cycle with the instructor.
- Work is pulled, not pushed. A member takes the next prioritized item only
  with capacity to finish it.
- A blocker MUST be raised in the team channel and in the Monday sync as
  soon as it stops progress.
- Quality gates on a backend pull request:
  - MUST: pytest unit tests for the change pass, with no `sleep()`.
  - MUST: router and dependency layout in Principle I is preserved.
  - MUST: contract or integration tests from Principle IV when the change
    crosses a boundary.
  - MUST NOT: treat a green unit suite as evidence that a latency budget
    is met. Budget stories need the experiment named in the test strategy.

## Governance

This constitution supersedes conflicting local practice for `apps/backend`.
Feature specs, plans, and tasks MUST be checked against it before
implementation. Complexity beyond this structure (extra services, a gateway
on a path whose budget was measured without one, a blocking provider call,
or a second copy of a domain rule) MUST be justified in the plan's
complexity record or it is rejected.

Amendments MUST go through a pull request with at least one reviewer, a
version bump, and a short migration note for any principle that changes
meaning. Versioning is semantic:

- MAJOR: a principle is removed or redefined so existing services would
  violate it.
- MINOR: a new principle or a material expansion of guidance.
- PATCH: clarification, wording, or non-semantic edits.

`RATIFICATION_DATE` is the date this document was first adopted.
`LAST_AMENDED_DATE` changes only when the constitution text changes.
Compliance is reviewed on every backend pull request against the principles
and both constraint sections above. The runtime guidance file is
`.specify/memory/constitution.md`.

**Version**: 1.0.0 | **Ratified**: 2026-10-01 | **Last Amended**: 2026-10-01
