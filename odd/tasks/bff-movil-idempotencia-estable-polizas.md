# bff-movil: clave de idempotencia estable al emitir póliza

## Objetivo

Que emitir una póliza desde el móvil se pueda reintentar tras una falla técnica sin quemar la cotización.

## Problema (revisado el 2026-11-21 durante las pruebas de emisión)

`POST /v1/cliente/polizas` de `bff-movil` genera `idempotency_key=str(uuid.uuid4())` en cada petición.
El flujo acepta la oferta, cobra la prima y emite la póliza; la aceptación se confirma antes de cobrar.
Si el cobro falla (por ejemplo, `ms-pagos` respondió 500), la cotización ya quedó `aceptada` y el
reintento llega con otra clave: `ms-cotizacion` responde `oferta_ya_usada` (422) y esa cotización no se
puede emitir nunca más, aunque el servicio ya se haya arreglado.

Es el mismo defecto que `bff-web` corrigió (`fix(bff-web): clave de idempotencia estable al emitir poliza`);
`bff-movil` no se había tocado.

## Alcance

Dentro: `apps/backend/bff-movil/app/routers/cliente.py` (`aceptar`) y su test.

Fuera: las otras dos claves `uuid4` del servicio (`/cotizaciones` y el flujo hipotecario) y los endpoints
que ya reciben la clave del cliente en la cabecera `Idempotency-Key`.

## Tareas

| ID | Tarea |
| --- | --- |
| T1 | Derivar la clave de aceptación de la cotización: `_uuid_desde("aceptacion-cliente", cotizacionId)`, con el mismo espacio de nombres y la misma etiqueta que `bff-web`, así que una misma cotización produce la misma clave en los dos canales. |
| T2 | Test: la clave se repite entre reintentos de la misma cotización, cambia con otra cotización y coincide con la derivación esperada. |

## Criterios de aceptación

- [x] El test nuevo falla con el código anterior (claves distintas por petición) y pasa con el arreglo.
- [x] Suite de `bff-movil` en verde: 115 pasan, 2 se saltan.
- [ ] Tras el despliegue: reintentar una emisión que falló por `ms-pagos` la retoma en vez de dar `oferta_ya_usada`.

## Limitaciones

- No rescata las cotizaciones que ya quedaron `aceptadas` con una clave aleatoria durante las pruebas: esas
  hay que volver a cotizar.
