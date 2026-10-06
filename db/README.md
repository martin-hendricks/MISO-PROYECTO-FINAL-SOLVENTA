# db — Schema del modelo de datos

DDL PostgreSQL del modelo de datos de Solventa (VC-004, wiki [§1.1.4.1 Modelo de datos](https://github.com/martin-hendricks/MISO-PROYECTO-FINAL-SOLVENTA/wiki/Hoja-de-trabajo-semana-8#11441-modelo-de-datos)).

## Estructura

Un archivo por schema; cada schema es el almacén propio de un microservicio y cada archivo es autocontenido (incluye su `CREATE SCHEMA`).

| Archivo | Schema | Tablas |
|---|---|---|
| `01_ms_identidad.sql` | `ms_identidad` | `usuario`, `sesion_token` |
| `02_ms_consentimiento.sql` | `ms_consentimiento` | `consentimiento_datos` |
| `03_ms_socios.sql` | `ms_socios` | `socio` |
| `04_ms_cotizacion.sql` | `ms_cotizacion` | `solicitud_cotizacion`, `regla_rating`, `oferta_seguro` |
| `05_ms_perfilamiento.sql` | `ms_perfilamiento` | `perfil_riesgo`, `fuente_dato_consultada` |
| `06_ms_suscripcion.sql` | `ms_suscripcion` | `suscripcion` |
| `07_ms_polizas.sql` | `ms_polizas` | `poliza`, `cobertura`, `prima`, `outbox_evento`* |
| `08_ms_siniestros.sql` | `ms_siniestros` | `reclamacion`, `evidencia_siniestro`, `evaluacion_siniestro` |
| `09_ms_pagos.sql` | `ms_pagos` | `medio_pago`, `pago`, `transaccion_pasarela` |
| `10_ms_parametrico.sql` | `ms_parametrico` | `evento_parametrico` |
| `11_analitica.sql` | `analitica` | `evento_analitico` |
| `12_notificaciones.sql` | `notificaciones` | `notificacion` |

\* Tabla técnica (patrón *transactional outbox*), no es entidad del dominio de VC-004.

## Convenciones

- **Nombres:** `snake_case` (el diagrama usa `camelCase`: `usuarioId` → `usuario_id`, `SesionToken` → `sesion_token`). Los atributos `timestamp` del diagrama se renombran para no usar una palabra reservada: `fuente_dato_consultada.consultada_en` y `evento_analitico.ocurrido_en`.
- **Tipos:** `uuid` → `UUID DEFAULT gen_random_uuid()`, `string` → `TEXT`, `decimal` → `NUMERIC(14,2)`, `float` → `DOUBLE PRECISION`, `datetime` → `TIMESTAMPTZ`, `json` → `JSONB`.
  - Excepción: `evento_parametrico.umbral` y `valor_observado` usan `NUMERIC(14,4)` porque son mediciones de telemetría, no montos.
- **FK dentro del mismo microservicio:** constraint `REFERENCES` real (p. ej. `ms_polizas.cobertura.poliza_id`).
- **FK marcadas `(ref)` en el diagrama (cruzan microservicios):** FK **lógica**: columna `UUID` + índice + `COMMENT` que indica el destino, **sin constraint**. Respeta "un almacén por servicio" (§1.1.4.4); la integridad se garantiza por eventos/validación en el servicio dueño.
- **Referencias opcionales** (`pago.prima_id`, `pago.reclamacion_id`, `evento_parametrico.reclamacion_id`) son nullable, con índice parcial. En `pago` exactamente una de las dos debe venir informada.
- **Unicidad** donde el dominio lo exige: documento y email de usuario (email sin distinguir mayúsculas), número de póliza, `idempotency_key` de transacción y `evento_externo_id` paramétrico (procesamiento exactamente una vez, EC-ESC-03).
- **Consentimiento:** `solicitud_cotizacion` y `fuente_dato_consultada` guardan el `consentimiento_id` que autorizó la consulta (`ConsentimientoToken` de `solicitudDTO`, VC-007).

## Eventos e idempotencia

- **Productor (`ms_polizas`):** la póliza y su `PolizaEmitidaEvent` se escriben en la misma transacción (`poliza` + `outbox_evento`). Un relay publica en Kafka las filas con `publicado_en IS NULL` y las marca; si el servicio cae entre el commit y la publicación, el evento se publica al reiniciar (entrega *al menos una vez*).
- **Consumidores (`analitica`, `notificaciones`):** guardan el id del evento de origen (`evento_origen_id`) con restricción `UNIQUE`, de modo que una reentrega se descarta con `INSERT ... ON CONFLICT DO NOTHING` (efecto *exactamente una vez*, §1.1.4.4 / EC-ESC-03).

## Instancias de base de datos

**Desarrollo local:** todos los schemas pueden convivir en una sola base de datos (ver *Ejecución*).

**Despliegue:** cada microservicio aplica únicamente su propio archivo sobre su almacén. Por la estrategia de replicación de §1.1.4.3, al menos estos dos almacenes deben vivir en **instancias RDS separadas**, porque su política de redundancia es distinta:

| Schema | Instancia | Redundancia |
|---|---|---|
| `ms_polizas` | RDS PostgreSQL propia | **Activa**: *read replica* en AZ-b que atiende lecturas (EC-LAT-10, RPO ≤ 30 s) |
| `ms_siniestros` | RDS PostgreSQL propia | **Pasiva**: *standby* Multi-AZ alimentado por el `Sincronizador`, sin tráfico; el `Monitor` la promueve (EC-DISP-06/07, RTO ≤ 10 min) |

## Ejecución

Requiere PostgreSQL 13+. Los archivos se ejecutan en orden numérico:

```bash
for f in db/schema/*.sql; do psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"; done
```

O montando la carpeta en un contenedor:

```bash
docker run --rm -e POSTGRES_PASSWORD=postgres -p 5432:5432 \
  -v "$PWD/db/schema:/docker-entrypoint-initdb.d:ro" postgres:16
```
