# bff-web

Backend for Frontend del canal web: contrato versionado para cotizar, emitir, gestionar y siniestros (HU-72). Valida JWT y autoriza por rol en servidor (HU-74/75).

**Stack:** Python (FastAPI)

Contrato: `specs/001-bff-unit-checks/contracts/bff-web.md`

## Contrato Pact con el núcleo (HU-88)

`bff-web` es consumidor de `ms-cotizacion`. `tests/contract/test_contrato_ms_cotizacion.py` declara el recorrido de catálogo, cotización, reconsulta, aceptación (aceptada y rechazada) y la consulta por oferta de la billetera, y genera `pacts/bff-web-ms-cotizacion.json`, que se versiona en el repo. Cada interacción exige solo los campos que leen las traducciones de `routers/cliente.py`: si el BFF empieza a leer un campo nuevo, el test falla hasta que se agregue al pacto.

```bash
pip install -e ".[test,contract]"
pytest -m contract
```

Después, `pytest -m contract` en `ms-cotizacion` verifica el pacto contra la app real. En CI ambos corren en el workflow `backend-contract-tests.yml`.

