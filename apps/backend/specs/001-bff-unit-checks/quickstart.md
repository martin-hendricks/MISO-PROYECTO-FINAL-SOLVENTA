# Quickstart: Channel Gateways and Merge Checks

Validate the gateways in the runner's Python process. Do not build an image and do not start a database.

## Prerequisites

- Python 3.10 or newer
- The repository checkout that contains `apps/backend`

## Run one gateway's checks

From `apps/backend/bff-web` (the same commands apply in `bff-movil`):

```bash
python -m pip install -e ".[test]"
python -c "from app.main import app"
pytest tests -m "not integration and not contract"
```

Expected:

- The import prints nothing and exits 0.
- `pytest` collects at least one test and exits 0.
- No test calls a domain service or sleeps.

Repeat for `apps/backend/bff-movil`.

## Scenarios that must pass

Use the paths in [contracts/bff-web.md](contracts/bff-web.md) and [contracts/bff-movil.md](contracts/bff-movil.md).

1. Web sign-in with `rol` `asesor` returns a token pair. Sign-in with any other role string returns 400.
2. Mobile sign-in has no `rol` field and the token is a customer token. A later mobile call that also sends `rol` still behaves as the customer.
3. A customer token on `GET /asesor/cartera` or `GET /operador/avisos` returns 403.
4. An advisor token on `POST /asesor/cotizaciones` returns the offer. The same token on `POST /operador/polizas/ciclo` returns 403.
5. An operator token on `POST /operador/polizas/ciclo` with `verbo` `cancelar` and no `motivo` returns 400. With `motivo`, the policy `estado` is `cancelada`.
6. `POST /cliente/polizas` with `cotizacionId` `COT-RECHAZADA` returns `estado` `rechazada`.
7. `GET /cliente/pagos-automaticos` on each gateway returns the same numeric `monto` and `moneda`, and no locale.
8. Mortgage with `consentimientoPerfil` `false` returns `degradada` `true` and does not wait.
9. Mobile registration with `pruebaDeVida` `no` is accepted. The request has no selfie field.
10. A claim notice with `geo` `null` is accepted.

## Workflow

The workflow file is `.github/workflows/backend-unit-tests.yml` at the git root.

- A pull request into `main` runs a gateway only when that gateway's files changed.
- A push to `main` runs both gateways even when their files did not change.
- Another directory under `apps/backend` runs only when it changed and already has a test file. A domain with no tests is skipped and the job stays green. The skip reason is in the job summary.
- The job fails if a selected tree contains `sleep(`, collects zero tests, or fails `pytest`.

## Branch protection (people apply this)

On `main`:

1. Require the unit-test status check.
2. Require at least one approving review.
3. Do not add a bot that changes these settings.

A skipped optional domain must not be configured as a separate required check.
