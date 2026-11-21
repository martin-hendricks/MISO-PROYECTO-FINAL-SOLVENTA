# bff-web

Backend for Frontend del canal web: contrato versionado para cotizar, emitir, gestionar y siniestros (HU-72). Valida JWT y autoriza por rol en servidor (HU-74/75).

**Stack:** Python (FastAPI)

Contrato: `specs/001-bff-unit-checks/contracts/bff-web.md`

## Socios del back-office

Alta, rotación y revocación de socios B2B para los roles `asesor` y `operador`. bff-web reenvía el token a ms-identidad (`/v1/socios`) y traduce a camelCase; los errores `{codigo, mensaje}` del núcleo (404, 409, 422) pasan tal cual.

| Ruta | Respuesta |
|------|-----------|
| `GET /v1/backoffice/socios` | `200 {socios: [{socioId, nombre, alcances, estado, creadoEn, credenciales: [{credencialId, creadaEn, revocadaEn}]}]}` |
| `POST /v1/backoffice/socios` `{nombre, alcances}` | `201 {socioId, nombre, alcances, estado, creadoEn, credencialId, apiKey}` |
| `POST /v1/backoffice/socios/{socioId}/credenciales` | `201 {credencialId, apiKey}` |
| `DELETE /v1/backoffice/socios/{socioId}/credenciales/{credencialId}` | `204` |
| `POST /v1/backoffice/socios/{socioId}/revocacion` | `200` con la vista del socio |

## Contrato Pact con el núcleo (HU-88)

`bff-web` es consumidor de `ms-cotizacion`. `tests/contract/test_contrato_ms_cotizacion.py` declara el recorrido de catálogo, cotización, reconsulta, aceptación (aceptada y rechazada) y la consulta por oferta de la lista de pólizas. `GET /v1/cliente/billetera` lee los depósitos en `ms-siniestros` (`GET /v1/pagos-recibidos`), y genera `pacts/bff-web-ms-cotizacion.json`, que se versiona en el repo. Cada interacción exige solo los campos que leen las traducciones de `routers/cliente.py`: si el BFF empieza a leer un campo nuevo, el test falla hasta que se agregue al pacto.

```bash
pip install -e ".[test,contract]"
pytest -m contract
```

Después, `pytest -m contract` en `ms-cotizacion` verifica el pacto contra la app real. En CI ambos corren en el workflow `backend-contract-tests.yml`.

`tests/contract/test_contrato_ms_siniestros_prestadores.py` declara las ciudades del país (cliente y operador), el área visible del mapa y el 422 `area_invalida`, y genera `pacts/bff-web-ms-siniestros.json`.

## Mapa de prestadores

- `GET /v1/cliente/prestadores/ciudades?pais=` y `GET /v1/operador/prestadores/ciudades?pais=` reenvían `con_prestadores=true` y `false`. El cliente solo ve ciudades con prestadores activos.
- `GET /v1/cliente/prestadores` y `GET /v1/cliente/siniestros/{id}/prestadores` aceptan `norte, sur, este, oeste`. Con área se pide `limite=500` al núcleo y no se manda `radioKm`; `lat`/`lng` solo fijan el origen de la distancia. La respuesta trae `truncado` y cada fila su `pais`.
- `GET /v1/operador/prestadores` acepta `pais`. Los 422 del núcleo (`pais_desconocido`, `ciudad_desconocida`, `area_invalida`, `limite_invalido`) pasan como `{codigo, mensaje}`.

