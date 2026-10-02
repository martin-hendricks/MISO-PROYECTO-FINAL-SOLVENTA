# Contract: bff-movil

Bodies match Contratos BFF. Paths are assigned by this plan. Unless noted, success is HTTP 200. A missing or invalid token is 401. An advisor or operator token is 403. A body that breaks a written rule is 400. A `rol` field on a protected body is ignored.

Only a customer token is accepted after sign-in.

## Public

| Action | Path | Request | Response |
| --- | --- | --- | --- |
| Sign in | `POST /sesion/ingreso` | `correo`, `contrasena` | `accessToken`, `refreshToken`, `expiraEn`. Role is customer. |
| Refresh | `POST /sesion/refresh` | `refreshToken` | Same token pair |
| Register | `POST /registro` | `nombre`, `apellidos`, `documento`, `correo`, `pruebaDeVida`, `habeasData` | Accepted registration. `pruebaDeVida` is `ok` or `no`. |
| Revoke consent | `POST /registro/consentimiento` | `{ "habeasData": false }` | Consent revoked |

The selfie is not a field.

## Customer

| Action | Path | Request | Response |
| --- | --- | --- | --- |
| Quote | `POST /cliente/cotizaciones` | `ramo`, `datosRiesgo` | Offer body |
| Re-read quote | `GET /cliente/cotizaciones/{cotizacionId}` | None | Same offer |
| Accept | `POST /cliente/polizas` | `cotizacionId` | Policy, or refusal when id is `COT-RECHAZADA` |
| Wallet | `GET /cliente/polizas` | None | `{ "polizas": [ ... ] }` |
| Policy detail | `GET /cliente/polizas/{numero}` | None | Policy fields plus `queHacer` |
| Claim notice | `POST /cliente/siniestros` | `poliza`, `fechaHecho`, `geo` or `null`, `adjuntos` | `siniestroId`, `estado` `recibido` |
| Claim list | `GET /cliente/siniestros` | None | `{ "siniestros": [ ... ] }` |
| Automatic payment | `GET /cliente/pagos-automaticos` | None | Same body as the web trace |
| Mortgage offer | `POST /cliente/oferta-hipotecaria` | `credito`, `consentimientoPerfil` | Ready or degraded offer |
| In-app notices | `GET /cliente/avisos` | None | `{ "avisos": [ ... ] }` |
| Home | `GET /cliente/inicio` | None | Home aggregate. `hipotecario` may be `null`. |
| Register push token | `POST /cliente/avisos/token` | `token`, `plataforma` | Accepted registration |
| Push payload | `GET /cliente/avisos/push` | None | `tipo`, `titulo`, `cuerpo`, `destino`, `poliza` |
| List providers | `GET /cliente/prestadores` | None | `{ "prestadores": [ ... ] }` |
| Request assistance | `POST /cliente/asistencias` | `prestadorId`, `geo`, `poliza` | `asistenciaId`, `estado` `registrada` |

Log out is `POST /sesion/salida` with an empty body and a customer token.

This gateway does not serve renew, modify, cancel, the operator queue, the advisor portfolio, the client file, or the assistance status.
