# Research: Channel Gateways and Merge Checks

## Decision: Two FastAPI packages, mocks only

**Decision**: Implement `apps/backend/bff-web` and `apps/backend/bff-movil` as separate FastAPI packages. Each returns the Contratos BFF bodies from in-process fixtures. Neither package calls a domain service, a database, a cache, a bus, or a cloud API.

**Rationale**: The spec requires those two gateways and forbids implementing `api-socios` and every `ms-*` service. The constitution requires one package per deployable service, with routers included from `app/main.py`.

**Alternatives considered**: One process with two mounted apps (rejects the existing service folders). A shared library imported by both gateways (adds a package this branch is not supposed to create, and the constitution forbids services importing one another's internals).

## Decision: Local mock tokens, validated in the gateway

**Decision**: Sign-in mints an HS256 bearer token inside the gateway. Claims are `sub` (email), `rol`, and `exp`. Validation is a single dependency, `get_current_caller`, used by protected routers. The signing secret comes from the environment variable `SOLVENTA_TOKEN_SECRET`. Tests set that variable; they do not read a cloud secret.

**Rationale**: Protected screens need a token the same gateway can check. `ms-identidad` is out of scope, so the gateway cannot call it. Keeping issuance behind one dependency lets a later change replace the signer without rewriting routers.

**Alternatives considered**: Unsigned tokens (any client could forge a role). Opaque random strings stored in memory (breaks when more than one process handles the same caller, and the published body already calls the token a JWT).

## Decision: Paths this plan assigns

**Decision**: Contratos BFF does not fix paths or verbs. This plan assigns the paths in `contracts/bff-web.md` and `contracts/bff-movil.md`. Prefixes do not end with `/`. Shared prefix, tag, and role dependency sit on the `APIRouter`. Bodies stay the published JSON.

**Rationale**: The spec allows planning to choose addresses as long as the bodies do not change.

**Alternatives considered**: Leaving paths unset until implementation (blocks tests and OpenAPI). Copying a bank or payment-provider schema (the contract page explicitly is not that schema).

## Decision: How a mock selects an alternate body

**Decision**: Alternates use fields the page already writes.

- Web sign-in `rol` outside `cliente`, `asesor`, `operador` is refused.
- Mobile registration `pruebaDeVida` of `no` is stored and returned; any other value except `ok` is refused. `{ "habeasData": false }` revokes consent.
- Quote id `COT-RECHAZADA` returns the written refusal body. Any other id returns the written offer, and accept-from-quote returns the written policy. Re-reading a quote id returns that same offer.
- A claim notice with `geo: null` is accepted and returns the written received body.
- Operator `decision` of `rechazar` without `motivo` is refused. `aprobar`, and `rechazar` with `motivo`, are accepted.
- Mortgage request with `consentimientoPerfil: false` returns `degradada: true` and fallback premium `50000` `COP`. `true` returns the written ready offer (`prima` `64000`, `degradada: false`). The page names a fallback amount but does not give the number.
- `verbo` `cancelar` without `motivo` is refused. `cancelar` with `motivo` returns the policy body with `estado` `cancelada`. `renovar` and `modificar` return that policy body with `estado` `vigente`.
- Client create omits `clienteId`. Deactivate sends the written `{ "clienteId", "estado": "inactivo" }` body.
- No route sleeps. The degraded premium is the only slow outcome.

**Rationale**: The spec requires every alternate body the page already writes, and forbids inventing bodies that the page only names (other lines of business) and forbids a timed pause.

**Alternatives considered**: A `?scenario=` query on every route (changes the contract the page did not write). A real delay (forbidden by the spec and by the constitution's ban on `sleep()` in checks).

## Decision: Role gates

**Decision**: Routers declare the allowed role once via a dependency.

- Web customer: quote without `clienteId`, issue and query, automatic-payment traceability, mortgage offer, web home.
- Web advisor: portfolio, client file, assisted sale (quote with `clienteId`).
- Web operator: claim queue, renew/modify/cancel, assistance status.
- Sign-in, refresh, and registration are public. Logout accepts any valid token for that gateway.
- Mobile accepts only `rol` `cliente`. A role field on a protected mobile body is ignored. Advisor and operator tokens are refused.

**Rationale**: This is the clarification recorded in the spec. Putting the role on the router avoids copying it onto every path.

**Alternatives considered**: One dependency that allows every valid token (rejected in clarification). Per-path role checks (duplicates the same rule).

## Decision: Duplicate the automatic-payment body

**Decision**: Both packages define the same automatic-payment model. Tests assert the JSON matches. Neither package imports the other.

**Rationale**: Both gateways must return that body, and they must not share internal modules.

**Alternatives considered**: A third schema package (new folder, out of scope for this branch).

## Decision: Unit checks in GitHub Actions, in process

**Decision**: Add `.github/workflows/backend-unit-tests.yml` at the git repository root (the parent of `apps/`). The job uses Python 3.10 or newer, installs each selected service from its own `pyproject.toml`, imports `app.main:app`, fails if `tests/` contains `sleep(`, and runs `pytest` excluding markers `integration` and `contract`. A JUnit report is always uploaded. Coverage may be uploaded and does not fail the job.

Selection:

- On a pull request into `main`, run `bff-web` or `bff-movil` only when that directory changed. Run another `apps/backend/*` directory only when it changed and `tests/` contains at least one test file.
- On a push to `main`, always run both gateways, even when neither directory changed. Optional domains still run only when they changed and already have tests.
- Pull requests and pushes that are not for `main` do not run this check.
- If an optional domain has tests but no `pyproject.toml` or no `app/main.py`, skip it and write the reason into the job summary. Do not fail the job for that skip.
- A selected service that collects zero tests fails the job.
- The job does not start containers, databases, or network services.

**Rationale**: Matches the spec's required and optional checks. `pytest` and `TestClient` exercise the ASGI app in the runner process, which is the constitution's unit-test rule. The workflow must live at the git root or GitHub will not run it.

**Alternatives considered**: Running the suite inside the future runtime image (does not prove the unit checks, and this branch has no image). Failing the job when a domain has no tests (blocks this branch). A coverage percentage gate (the spec forbids it). Triggering on `develop` (the spec says that branch is not used).

## Decision: Integrate on main

**Decision**: Short-lived branches merge to `main` under trunk-based or GitLab flow. The workflow `on` block is pull requests targeting `main` and pushes to `main`. Branch protection for people is documented against `main`.

**Rationale**: The spec clarification of 2026-10-01 names `main` as the only integration branch. Both chosen flows share that branch. GitLab flow does not add a second long-lived branch for this check.

**Alternatives considered**: GitFlow with `develop` (rejected by the spec). A production branch in addition to `main` (not requested; this check does not deploy).

## Decision: Branch protection is a human note

**Decision**: Document the `main` rule in `quickstart.md`: the unit-test check is required, and one teammate must approve. Do not add a bot that changes repository settings.

**Rationale**: The spec requires the rule to be recorded and forbids automating it.
