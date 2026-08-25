# HA-08 — Modelo de lectura de baja latencia para el estado de siniestro

Experimento de arquitectura que evalúa si CQRS con proyección materializada y
caché permite cumplir el ASR **EC-LAT-11** (p95 ≤ 150 ms) en la consulta de
estado de siniestro, y cuál es el **nivel mínimo de complejidad** que lo logra.

| | |
|---|---|
| **Historia de arquitectura** | HA-08 |
| **Escenario de calidad** | EC-LAT-11 — Latencia, prioridad (A,A) — ASR |
| **Hipótesis** | HD-08 (sub-hipótesis HD-08.1 a HD-08.4) |
| **Estado** | 🚧 Estructura creada — implementación pendiente |

## Documentación

- [Diseño del experimento](../../docs/experiments/ha-08/Diseno_Experimento_HA-08.md) — hipótesis, variables, criterios de aceptación y amenazas a la validez.
- [Guía técnica](../../docs/experiments/ha-08/Guia_Tecnica_HA-08.md) — Docker, esquemas, código, dataset y protocolo de corridas.

**Ambos documentos son la fuente de verdad.** Este README solo explica cómo
operar la carpeta; no duplica el diseño ni el protocolo.

## Los cuatro brazos

Los cuatro se ejecutan **sobre el mismo binario**, seleccionados por
`READ_STRATEGY`, para que la estrategia de lectura sea la única variable.

| Brazo | Estrategia | Camino de lectura |
|---|---|---|
| `A` | Línea base | PostgreSQL `siniestros_w` → 5 joins + agregaciones |
| `B` | CQRS | PostgreSQL `siniestros_r` → `SELECT payload WHERE siniestro_id = $1` |
| `C` | CQRS + caché | Redis (acierto) / proyección + `SETEX` (fallo) |
| `C_PRIME` | C sin re-serialización | Devuelve los bytes cacheados sin revalidar |

## Prerequisitos

- Docker Desktop con **Docker Compose V2**
- 16 GB de RAM, 4 núcleos y **20 GB de disco libre** (el dataset sintético de
  1 000 000 de siniestros ocupa ~2 GB más índices)
- **Git Bash** en Windows: los scripts de `scripts/` son `.sh`. Ejecutarlos
  desde PowerShell falla; usar `bash scripts/run_experiment.sh …`.

## Puesta en marcha

```bash
cd experiments/ha-08-cqrs-read-model
cp .env.example .env
docker compose up -d
```

Todos los comandos de la guía técnica asumen **esta carpeta** como directorio
de trabajo. El protocolo completo de corridas está en la sección 11 de la guía.

## Estructura

```
api/              FastAPI + Uvicorn — los cuatro brazos en un solo binario
projector/        Consumidor aiokafka — upsert idempotente + invalidación
simulator/        Proceso de evaluación sintético (~5 eventos/s)
db/init/          Esquemas siniestros_w y siniestros_r, seed y backfill
load/k6/          Script de carga con ejecutor de tasa de llegada
observability/    Prometheus + Grafana
scripts/          run_experiment.sh, verify_parity.sh, collect_results.sh
results/raw/      Salidas crudas por corrida (ignoradas por git)
```

## Advertencias de medición

Este experimento **mide latencia**: cualquier ruido en el host contamina el
resultado.

- **El repositorio está dentro de OneDrive.** Los volúmenes de PostgreSQL,
  Redis y Grafana deben ser *named volumes* de Docker, **nunca bind mounts
  dentro del repo**: OneDrive sincronizaría gigabytes durante la corrida y
  degradaría justamente lo que se está midiendo. `results/raw/` y los datos de
  contenedores ya están en `.gitignore`.
- **No versionar `.env`.** Cambia entre brazos y corridas; es el registro de
  qué se ejecutó, y va en el informe, no en git.
- **Cerrar aplicaciones pesadas durante las corridas.** El generador de carga,
  el broker y la base compiten por la misma CPU (ver Anexo D del diseño).
- **Verificar la paridad del payload antes de cada corrida**
  (`scripts/verify_parity.sh`). Si los brazos no devuelven el mismo JSON, la
  comparación queda invalidada.

## Resultados

Las plantillas de registro están en el Anexo C del documento de diseño. Las
salidas crudas van a `results/raw/` (ignoradas); solo los consolidados que se
citan en el informe se versionan.
