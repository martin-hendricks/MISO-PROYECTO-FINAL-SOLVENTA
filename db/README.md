# db — Schema del modelo de datos

DDL PostgreSQL del modelo de datos de Solventa (VC-004, wiki [§1.1.4.1 Modelo de datos](https://github.com/martin-hendricks/MISO-PROYECTO-FINAL-SOLVENTA/wiki/Hoja-de-trabajo-semana-8#11441-modelo-de-datos)).

## Estructura

Un archivo por schema; cada schema es el almacén propio de un microservicio.

| Archivo | Schema | Tablas |
|---|---|---|
| `00_schemas.sql` | — | `CREATE SCHEMA` de todos los almacenes |
| `01_ms_identidad.sql` | `ms_identidad` | `usuario`, `sesion_token` |
| `02_ms_consentimiento.sql` | `ms_consentimiento` | `consentimiento_datos` |
| `03_ms_socios.sql` | `ms_socios` | `socio` |
| `04_ms_cotizacion.sql` | `ms_cotizacion` | `solicitud_cotizacion`, `regla_rating`, `oferta_seguro` |
| `05_ms_perfilamiento.sql` | `ms_perfilamiento` | `perfil_riesgo`, `fuente_dato_consultada` |
| `06_ms_suscripcion.sql` | `ms_suscripcion` | `suscripcion` |
| `07_ms_polizas.sql` | `ms_polizas` | `poliza`, `cobertura`, `prima` |
| `08_ms_siniestros.sql` | `ms_siniestros` | `reclamacion`, `evidencia_siniestro`, `evaluacion_siniestro` |
| `09_ms_pagos.sql` | `ms_pagos` | `medio_pago`, `pago`, `transaccion_pasarela` |
| `10_ms_parametrico.sql` | `ms_parametrico` | `evento_parametrico` |
| `11_analitica.sql` | `analitica` | `evento_analitico` |
| `12_notificaciones.sql` | `notificaciones` | `notificacion` |

## Convenciones

- **Nombres:** `snake_case` (el diagrama usa `camelCase`: `usuarioId` → `usuario_id`, `SesionToken` → `sesion_token`).
- **Tipos:** `uuid` → `UUID DEFAULT gen_random_uuid()`, `string` → `TEXT`, `decimal` → `NUMERIC(14,2)`, `float` → `DOUBLE PRECISION`, `datetime` → `TIMESTAMPTZ`, `json` → `JSONB`.
- **FK dentro del mismo microservicio:** constraint `REFERENCES` real (p. ej. `ms_polizas.cobertura.poliza_id`).
- **FK marcadas `(ref)` en el diagrama (cruzan microservicios):** FK **lógica**: columna `UUID` + índice + `COMMENT` que indica el destino, **sin constraint**. Respeta "un almacén por servicio" (§1.1.4.4); la integridad se garantiza por eventos/validación en el servicio dueño.
- **Referencias opcionales** (`pago.prima_id`, `pago.reclamacion_id`, `evento_parametrico.reclamacion_id`) son nullable, con índice parcial.
- Restricciones de unicidad añadidas donde el dominio lo exige: documento y email de usuario, número de póliza, `idempotency_key` de transacción y `evento_externo_id` paramétrico (procesamiento exactamente una vez, EC-ESC-03).

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

En despliegue, cada microservicio aplica únicamente su propio archivo (junto con su `CREATE SCHEMA`) sobre su almacén.
