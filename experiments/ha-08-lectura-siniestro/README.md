# Experimento HA-08 — Modelo de lectura de baja latencia para el estado de siniestro

Evalúa si CQRS (proyección materializada + caché) permite cumplir `EC-LAT-11` (p95 ≤ 150ms) en la consulta de estado de siniestro, y determina el nivel mínimo de complejidad necesario.

Diseño completo, hipótesis, criterios de aceptación y amenazas a la validez: `Diseno_Experimento_HA-08.md` en la wiki.
Guía técnica de montaje: `Guia_Tecnica_HA-08.md` en la wiki.

Bitácora técnica de la ejecución: [`INFORME.md`](INFORME.md).
Auditoría del experimento (verificación de cifras, brechas frente al diseño y coherencia con la arquitectura de semana 5): [`AUDITORIA_EXTERNA_HA-08.md`](AUDITORIA_EXTERNA_HA-08.md).

**Estado:** ejecutado. Protocolo formal (9 corridas contrabalanceadas) corrido el 2026-09-09/10; resultados consolidados en `results/consolidado.csv` y evidencia en `results/`. Pendientes antes de darlo por cerrado: ver [`INFORME.md`](INFORME.md) §5.

Montaje autocontenido y aislado de las apps de producto (`apps/`) — no depende de `ms-siniestros` real. Es un spike desechable de arquitectura, no un despliegue de producto.

---

## Cómo ejecutar el experimento

### Prerrequisitos

- Docker Desktop corriendo, con al menos 4 CPU y ~8 GB asignados a la VM (el compose reserva 2 CPU para Postgres y 2 para la API).
- `jq`, `curl` y `python3` en el host: los scripts los usan para las aserciones y para consolidar resultados.
- Ejecutar **siempre desde la raíz del experimento** (este directorio). Los scripts usan rutas relativas (`results/raw`, `load/k6`, `$(pwd)`) y fallan desde otro directorio.

```bash
cd experiments/ha-08-lectura-siniestro
```

### 1. Levantar el montaje y sembrar el dataset

```bash
docker compose up -d postgres redis redpanda prometheus grafana
```

Los `.sql` de `db/init/` corren automáticamente **solo la primera vez**, cuando el volumen `pgdata` está vacío. Es el paso largo: `03_seed.sql` genera 1.000.000 de siniestros con sus pólizas, 5 hitos, 3 documentos y 1 peritaje cada uno, y `04_backfill_projection.sql` precarga la proyección para que los brazos B y C no arranquen midiendo fallos masivos que no ocurrirían en producción.

```bash
docker compose ps                  # esperar a que postgres esté (healthy)
docker compose logs -f postgres    # seguir el avance del seed
```

Para re-sembrar desde cero: `docker compose down -v` (borra `pgdata` y vuelve a disparar los scripts de init).

```bash
docker compose up -d api projector simulator
curl -s localhost:8000/health | jq   # debe responder con el brazo activo
```

### 2. Verificar paridad de payload — una sola vez, antes de toda la serie

```bash
./scripts/verify_parity.sh
```

Compara el JSON que devuelven A, B y C para el mismo siniestro. Si difieren, parte de la latencia medida vendría del tamaño de la respuesta y la comparación entre brazos queda invalidada.

> **No invocar este script dentro de una corrida.** Recrea el contenedor `api` con A, B y C en un bucle y lo deja sirviendo el último brazo (C). Ese error invalidó las 12 corridas del 2026-09-08 —todas terminaron midiendo el brazo C— y por eso `run_experiment.sh` incluye una aserción dura contra `/health` en su paso 3. Ver [`INFORME.md`](INFORME.md) §0.

### 3. Prueba de humo (recomendado antes de comprometer horas)

```bash
docker compose --profile load run --rm \
  -e RUN_ID=smoke --entrypoint k6 k6 \
  run --out experimental-prometheus-rw /scripts/smoke_test.js
```

20 s a 10 req/s. Solo confirma que la cadena k6 → API → Prometheus (remote-write) funciona; **no** es el protocolo formal.

### 4. Correr las corridas

Corrida individual — `run_experiment.sh <A|B|C|C_PRIME> <run_id> [ttl_segundos]`:

```bash
./scripts/run_experiment.sh A r1
```

Cada corrida reinicia el estado volátil (FLUSHALL en Redis, restart de Postgres), levanta el brazo indicado, verifica contra `/health` que la API sirve ese brazo, lanza k6 con los escalones de 10/25/50/80 req/s (~13 min, con el primer minuto de calentamiento que se descarta en el análisis), captura `docker stats` en serie y recolecta al final el lag del proyector y los contadores de caché.

> Los contadores `ha08_cache_hits_total` / `misses_total` viven en el proceso de la API y se reinician cuando el contenedor se recrea (es decir, en la corrida siguiente). Si no se capturan al final de cada corrida —como hace el paso 5 del script— el hit-rate ya no es recuperable.

Series completas:

```bash
./scripts/run_serie_completa.sh      # 9 corridas del cuadrado latino (R1=A→B→C, R2=B→C→A, R3=C→A→B)
./scripts/run_serie_ttl.sh           # sensibilidad a TTL: brazo C con 0s y 300s, n=3 cada uno
./scripts/run_serie_alta_carga.sh    # iteración de alta carga 150/300/600 req/s, brazos A/B/C
```

Todas usan `set -euo pipefail` y se detienen a la primera aserción fallida, en vez de seguir produciendo datos inválidos.

Corrida de validación de los hallazgos V1/V3/V6 de la auditoría (brazo A con `shared_buffers=64MB` y hot set disperso):

```bash
./scripts/run_validacion_v1_v3.sh
# deja Postgres con shared_buffers=64MB — restaurar después con:
docker compose up -d --force-recreate postgres
```

### 5. Consolidar resultados

```bash
./scripts/collect_results.sh > results/consolidado.csv
```

Produce el CSV con las columnas de la plantilla de registro del Anexo C del diseño (brazo, corrida, p50/p95/p99, error, hit-rate, lag). Excluye deliberadamente las corridas inválidas del 2026-09-08 y las `ttl0_r1` / `ttl300_r1` contaminadas por contención de host, y marca las repeticiones en la columna `estado`.

Grafana queda en `localhost:3000` (acceso anónimo, o `admin`/`admin`) y Prometheus en `localhost:9090`.

### Puertos y endpoints útiles

| Servicio | Puerto | Endpoint |
|---|---|---|
| API de consulta | 8000 | `/siniestros/{id}/estado`, `/health`, `/metrics` |
| Proyector | 8001 | `/metrics` (incluye `ha08_projection_lag_seconds`) |
| Prometheus | 9090 | |
| Grafana | 3000 | |
| PostgreSQL | 5432 | esquemas `siniestros_w` (escritura) y `siniestros_r` (proyección) |
| Redis | 6379 | |
| Redpanda | 9092 | tópico `siniestros.eventos` |
