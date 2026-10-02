# Data Model: Channel Gateways and Merge Checks

Fixtures live in each gateway. Nothing in this feature is stored in a database. Field names match Contratos BFF.

## Caller session

| Field | Rules |
| --- | --- |
| correo | Any non-empty email at mock sign-in |
| contrasena | Any non-empty password at mock sign-in. It is not stored. |
| rol | Web: `cliente`, `asesor`, or `operador`. Mobile sign-in has no role field and always yields `cliente`. |
| accessToken | Bearer token carrying `sub`, `rol`, and `exp` |
| refreshToken | Bearer token used only by the refresh call |
| expiraEn | Seconds until expiry. The published example is `900`. |

A token is valid until `exp`. Refresh accepts the refresh token and returns a new pair. Logout has an empty body and requires a valid access token for that gateway.

Public calls: web and mobile sign-in, refresh, and registration. Every other call requires a valid access token.

## Desk role and screens

| Role | May call | Refused |
| --- | --- | --- |
| cliente (web) | Quote without `clienteId`, issue and query, automatic-payment traceability, mortgage offer, web home | Portfolio, client file, assisted sale, operator queue, policy commands, assistance status |
| asesor | Portfolio, client file, assisted sale (quote with `clienteId`) | Every other protected web screen |
| operador | Operator queue, renew / modify / cancel, assistance status | Every other protected web screen |
| cliente (mobile) | Every mobile protected contract | A role sent on the body is ignored. `asesor` and `operador` tokens are refused. |

## Money

| Field | Rules |
| --- | --- |
| prima or monto | Integer. Never a formatted string. |
| moneda | Currency code. The published examples use `COP`. |
| locale | Must not appear. |

Ready mortgage premium: `prima` `64000`, `degradada` `false`. Fallback premium, used when `consentimientoPerfil` is `false`: `prima` `50000`, `moneda` `COP`, `degradada` `true`.

## Screen payloads

Relationships are by identifier only (`cotizacionId`, `numero`, `siniestroId`, `clienteId`, `asistenciaId`). Identifiers in success fixtures are the examples on the contract page.

### Quote

Request: `ramo`, `datosRiesgo`. Assisted sale adds `clienteId`. Only the device `datosRiesgo` body is defined. Other lines of business named on the page are not given bodies and are not implemented.

Response: `cotizacionId`, `ramo`, `estado` `oferta_vigente`, `prima`, `moneda`, `venceEn`. Re-reading by `cotizacionId` returns the same body. `COT-RECHAZADA` is the refusal trigger for accept, not a different offer shape.

### Policy

Accept request: `cotizacionId`. Success: `numero`, `ramo`, `estado` `vigente`, `venceEn`. Refusal: `estado` `rechazada`, `motivo` "Valor del equipo fuera de rango".

Wallet: `polizas[]` of `numero`, `ramo`, `resumen`, `estado`, `venceEn`. Detail adds `queHacer`. The wallet body does not change when the phone was offline.

Command request: `numero`, `verbo` (`renovar`, `modificar`, `cancelar`), and `motivo` when cancelling. Response is the policy object. `cancelar` sets `estado` `cancelada`. `renovar` and `modificar` leave `estado` `vigente`.

### Claim notice

Request: `poliza`, `fechaHecho`, `geo` or `null`, `adjuntos[]` of `tipo` and `nombre`. `geo` has `lat`, `lng`, `precisionM`. Create response: `siniestroId`, `estado` `recibido`. List item: `siniestroId`, `ramo`, `resumen`, `estado`. Allowed `estado` values: `recibido`, `en_evaluacion`, `decidido`, `enrutado`, `pagado`.

Operator queue item: `siniestroId`, `poliza`, `ramo`, `estado`. Decision: `siniestroId`, `decision` (`aprobar` or `rechazar`), `motivo` required for `rechazar`. Assistance status must not appear in this queue.

### Automatic payment

Same body on both gateways: `siniestroId`, `poliza`, `umbral`, `monto`, `moneda`, `estado` `pagado`.

### Mortgage offer

Request: `credito.valor`, `credito.plazoMeses`, `consentimientoPerfil`. Response: `ramo`, `estado`, `prima`, `moneda`, `factores`, `degradada`.

### Home

`ofertaVigente`, `poliza`, `siniestroEnCurso`, `hipotecario`. The mobile example uses the written cards. The web response is the same aggregate for the desktop client. `hipotecario` may be `null`.

### Registration

Web: `nombre`, `apellidos`, `documento`, `correo`, `habeasData`. Mobile adds `pruebaDeVida` (`ok` or `no`). The selfie is never a field. Revoke: `{ "habeasData": false }`.

### Client file

Client: `clienteId`, `nombre`, `documento`, `correo`, `habeasData`, `estado`. Create and edit omit `clienteId`. Deactivate: `clienteId`, `estado` `inactivo`.

### Advisor portfolio

`kpis.cotizaciones`, `kpis.polizas`, and `cola[]` of `id`, `tipo`, `ramo`, `estado`.

### Notices

In-app list: `avisos[]` of `tipo`, `poliza`, and either `venceEn` or `estado`. Push registration: `token`, `plataforma`. Push payload: `tipo`, `titulo`, `cuerpo`, `destino`, `poliza`. Allowed `tipo`: `pago_automatico`, `vencimiento`, `renovacion`, `estado_siniestro`. Allowed `destino`: `parametrico`, `aviso-vencimiento`, `aviso-renovacion`, `detalle-siniestro`. One written payload is returned; the other enum values are constraints, not extra unpublished bodies.

### Assistance

Customer request: `prestadorId`, `geo`, `poliza`. Response: `asistenciaId`, `estado` `registrada`. Provider list: `prestadores[]` of `id`, `nombre`, `distanciaKm`, `zona`. Operations read: `asistenciaId`, `prestadorId`, `poliza`, `estado`.

## Check result

Not a gateway entity. The workflow records one result per selected service.

| Outcome | When |
| --- | --- |
| pass | Selected service imports, has tests, and `pytest` succeeds |
| fail | Import fails for a required gateway, `sleep(` is present, zero tests are collected, or `pytest` fails |
| skip | Optional domain is unchanged, has no tests, has tests but no package file, or has tests but no application module. The reason is visible. A skip does not fail the check. |
