# Contract: bff-web

Bodies match Contratos BFF. Paths are assigned by this plan. Unless noted, success is HTTP 200. A missing or invalid token is 401. A token with the wrong role is 403. A body that breaks a written rule is 400.

Role groups: customer `cliente`, advisor `asesor`, operator `operador`.

## Public

| Action | Path | Request | Response |
| --- | --- | --- | --- |
| Sign in | `POST /sesion/ingreso` | `correo`, `contrasena`, `rol` | `accessToken`, `refreshToken`, `expiraEn` |
| Refresh | `POST /sesion/refresh` | `refreshToken` | Same token pair |
| Register | `POST /registro` | `nombre`, `apellidos`, `documento`, `correo`, `habeasData` | Accepted registration |

`rol` must be `cliente`, `asesor`, or `operador`. Any email and password are accepted.

## Any valid web role

| Action | Path | Request | Response |
| --- | --- | --- | --- |
| Log out | `POST /sesion/salida` | Empty | Accepted logout |

## Customer

| Action | Path | Request | Response |
| --- | --- | --- | --- |
| Quote | `POST /cliente/cotizaciones` | `ramo`, `datosRiesgo`. `clienteId` must be absent. | Offer: `cotizacionId`, `ramo`, `estado`, `prima`, `moneda`, `venceEn` |
| Re-read quote | `GET /cliente/cotizaciones/{cotizacionId}` | None | Same offer |
| Issue | `POST /cliente/polizas` | `cotizacionId` | Policy, or refusal when id is `COT-RECHAZADA` |
| Wallet | `GET /cliente/polizas` | None | `{ "polizas": [ ... ] }` |
| Policy detail | `GET /cliente/polizas/{numero}` | None | Policy fields plus `queHacer` |
| Payment trace | `GET /cliente/pagos-automaticos` | None | Automatic-payment body |
| Mortgage offer | `POST /cliente/oferta-hipotecaria` | `credito`, `consentimientoPerfil` | Ready offer, or degraded offer when consent is false |
| Home | `GET /cliente/inicio` | None | `ofertaVigente`, `poliza`, `siniestroEnCurso`, `hipotecario` |

## Advisor

| Action | Path | Request | Response |
| --- | --- | --- | --- |
| Assisted sale | `POST /asesor/cotizaciones` | `clienteId`, `ramo`, `datosRiesgo` | Same offer body as the customer quote |
| Portfolio | `GET /asesor/cartera` | None | `kpis`, `cola` |
| List clients | `GET /asesor/clientes` | None | `{ "clientes": [ ... ] }` |
| Create client | `POST /asesor/clientes` | Client fields without `clienteId` | Client |
| Deactivate client | `POST /asesor/clientes/estado` | `clienteId`, `estado` `inactivo` | Deactivated client |

## Operator

| Action | Path | Request | Response |
| --- | --- | --- | --- |
| Claim queue | `GET /operador/avisos` | None | `{ "avisos": [ ... ] }` without assistance rows |
| Decide claim | `POST /operador/avisos/decision` | `siniestroId`, `decision`, `motivo` if rejecting | Accepted decision. 400 when `rechazar` has no `motivo` |
| Policy command | `POST /operador/polizas/ciclo` | `numero`, `verbo`, `motivo` if cancelling | Policy body with the new `estado`. 400 when `cancelar` has no `motivo` |
| Assistance status | `GET /operador/asistencias/{asistenciaId}` | None | `asistenciaId`, `prestadorId`, `poliza`, `estado` |

`verbo` is `renovar`, `modificar`, or `cancelar`. `decision` is `aprobar` or `rechazar`.

## Shared automatic-payment body

`siniestroId`, `poliza`, `umbral`, `monto` (number), `moneda`, `estado` `pagado`. No locale and no formatted amount. The mobile gateway returns this same body from its own route.
