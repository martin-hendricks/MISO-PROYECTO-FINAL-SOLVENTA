# bff-movil

Backend for Frontend del canal móvil: payloads acotados para aviso, pólizas, billetera de depósitos (`GET /cliente/billetera`) y cotización (HU-73). Valida JWT y autoriza por rol en servidor (HU-76/77), ignorando roles enviados desde el cliente.

**Stack:** Python (FastAPI)

Contrato: `specs/001-bff-unit-checks/contracts/bff-movil.md`

## Contrato Pact con el núcleo (HU-88)

`bff-movil` es consumidor de `ms-cotizacion`. `tests/contract/test_contrato_ms_cotizacion.py` declara la cotización (y su rechazo 422), la reconsulta, la aceptación (aceptada y rechazada) y la consulta por oferta de la billetera, incluido el 404 que la billetera tolera. Genera `pacts/bff-movil-ms-cotizacion.json`, que se versiona en el repo. Cada interacción exige solo los campos que leen las traducciones de `routers/cliente.py`: si el BFF empieza a leer un campo nuevo, el test falla hasta que se agregue al pacto.

```bash
pip install -e ".[test,contract]"
pytest -m contract
```

Después, `pytest -m contract` en `ms-cotizacion` verifica el pacto contra la app real. En CI ambos corren en el workflow `backend-contract-tests.yml`.

`tests/contract/test_contrato_ms_siniestros_prestadores.py` declara las ciudades del país, el área visible del mapa y el 422 `area_invalida`, y genera `pacts/bff-movil-ms-siniestros.json`.

## Mapa de prestadores

- `GET /v1/cliente/prestadores/ciudades?pais=` devuelve las ciudades con prestadores activos del país, con `lat`/`lng` como números.
- `GET /v1/cliente/prestadores` y `GET /v1/cliente/siniestros/{id}/prestadores` aceptan `norte, sur, este, oeste`. Con área se pide `limite=500` al núcleo y no se manda `radioKm`. La respuesta trae `truncado` y cada fila su `pais`.
- Sin el prefijo `/v1` las dos rutas devuelven la muestra fija (`pais: "CO"`, `truncado: false`).
