# Informe de ejecución — Experimento HA-08

**Modelo de lectura de baja latencia para el estado de siniestro (CQRS)**

Diseño completo: `Diseno_Experimento_HA-08.md` (wiki, `files/`). Guía técnica: `Guia_Tecnica_HA-08.md` (wiki, `files/`).

**Fecha de ejecución (protocolo formal, válida):** 2026-09-09/10. **Ejecución original invalidada:** 2026-09-08 — ver §0.
**Ambiente:** Docker Compose local (`experiments/ha-08-lectura-siniestro/`)
**Dataset:** 1.000.000 siniestros, 1.000.000 pólizas, 5.000.000 hitos, 3.000.000 documentos, 1.000.000 peritajes — verificado que supera `shared_buffers + effective_cache_size` (3.000 MB vs. 768 MB configurados)

---

## 0. Invalidación de las 12 corridas del 2026-09-08 y corrección aplicada

Una evaluación externa (`EVALUACION_EJECUCION_HA-08.md`, 2026-09-10) detectó un defecto que **invalida las secciones 1 y 2 de este informe tal como fueron redactadas originalmente**: `scripts/verify_parity.sh` recorre `for ARM in A B C` recreando el contenedor `api` en cada iteración para comparar payloads, y quedaba arrancado con el **último** brazo del bucle (**C**). `run_experiment.sh` invocaba esa verificación *dentro de cada corrida* (paso 3), después de levantar el brazo correcto (paso 2) y sin volver a levantarlo antes de medir con k6 (paso 4). Consecuencia verificada: **las 12 corridas del protocolo formal midieron todas el brazo C**, sin importar la etiqueta A/B/C del archivo de resultados. El único resultado real de esa sesión es una medición válida de C (cumple `EC-LAT-11` con ~30× de margen); A y B nunca se ejecutaron.

**Verificación de la causa raíz** (no solo se aceptó el reporte externo, se reprodujo):
- `results/evidencia/verify_parity_20260907_205420.log` muestra el patrón `Recreate → Recreated → Started` ×3 dentro de cada corrida — la huella del bug.
- Se reprodujo manualmente: tras correr `verify_parity.sh` una vez, `curl localhost:8000/health` devuelve `{"arm":"C"}` sin importar qué brazo se pretendía medir a continuación.
- `main.py:36` confirma que el endpoint de estado lee `settings.read_strategy` del proceso en ejecución en cada request — no una copia fijada al inicio del script — así que el binario servía genuinamente C, no era un error de etiquetado posterior.

**Corrección aplicada** (`scripts/run_experiment.sh`, `scripts/run_experiment_alta_carga.sh`, `scripts/verify_parity.sh`):
1. `verify_parity.sh` ya no se invoca dentro de cada corrida — se documenta que debe correrse **una sola vez antes de toda la serie**.
2. Se añadió una aserción dura en el paso 3 de ambos scripts de orquestación: `ARM_ACTIVO=$(curl -s localhost:8000/health | jq -r .arm)` seguido de `[ "$ARM_ACTIVO" = "$ARM" ] || exit 1`. Cualquier corrida futura donde la API no esté sirviendo el brazo esperado corta inmediatamente con un mensaje explícito, en vez de producir datos silenciosamente inválidos.
3. Validado con pruebas reales: (a) se reprodujo el escenario roto exacto y se confirmó que la aserción lo detecta y corta; (b) se confirmó el camino feliz — tras levantar la API en A, `/health` reporta `A` y un `GET` directo a Redis confirma que esa key nunca fue escrita (coherente con que `arm_a.py` no importa `cache`).

**Mejoras adicionales aplicadas antes de repetir la serie** (hallazgos §3.1 y §3.3 de la evaluación externa):
- `load/k6/read_estado.js` ahora taggea cada request con su **escalón** (`warmup`/`r10`/`r25`/r50`/`r80`, vía `k6/execution` y el tiempo transcurrido del escenario) y con **`calor`** (`caliente`/`frio`, según si el ID cae en el *hot set* de 10K o no). Como el output `experimental-prometheus-rw` de k6 exporta todos los tags de un `Trend` como labels de Prometheus, esto permite recuperar el p95 por escalón y segregado caliente/frío con PromQL, sin rehacer el pipeline de corridas:
  ```promql
  histogram_quantile(0.95, sum(rate(k6_ha08_estado_duration_bucket[1m])) by (le, escalon, arm, run_id))
  histogram_quantile(0.95, sum(rate(k6_ha08_estado_duration_bucket[1m])) by (le, calor, arm, run_id))
  ```
- Las duraciones de los escalones (1m + 3m×4) **no cambiaron** — se verificó con `k6 inspect` que el JSON de `scenarios` generado es idéntico al original.

**La iteración de alta carga (§2.4) también quedó invalidada por el mismo defecto.** `scripts/run_experiment_alta_carga.sh` es una copia de `run_experiment.sh` con el mismo paso 3 (`./scripts/verify_parity.sh` dentro de la corrida, sin aserción); su log (`results/raw/log_alta_carga_A.txt`) muestra la misma secuencia `Recreate`×2 (B, C — la primera iteración del bucle, A, no recrea porque coincide con el brazo que el paso 2 ya había levantado) inmediatamente antes de k6. La única señal que sugería lo contrario —CPU de `ha08-api` en 16.8% para "A" contra 0.7% para "B"/"C"— **no es prueba suficiente**: no se capturó el hit-rate de Redis en el momento de esa corrida (dato no recuperable retroactivamente), y esa diferencia de CPU podría deberse igual a un transitorio de arranque en frío del contenedor recién recreado. Ante la duda, se trata como inválida por el mismo mecanismo verificado en el protocolo formal, no se asume una excepción sin evidencia directa.

**Pendiente:** repetir las 9 corridas contrabalanceadas (+ TTL con n=3 en vez de n=1, hallazgo §3.7) **y la iteración de alta carga**, todas con el script corregido, y solo entonces re-redactar §1/§2/§2.4 con datos donde A y B realmente se ejecutaron. Ver checklist actualizado en §5.

---

## 1. Resultados consolidados

**Estos son los resultados válidos de las 9 corridas contrabalanceadas (2026-09-09/10), con el script corregido y la aserción de brazo activa en las 9 — ninguna falló.**

| Brazo | Corrida | p50 (ms) | p95 (ms) | max (ms) | Error (%) |
|---|---|---:|---:|---:|---:|
| A | r1 | 2.63 | 8.65 | 51.71 | 0 |
| B | r1 | 2.63 | 6.44 | 47.75 | 0 |
| C | r1 | 2.84 | 6.77 | 261.15 | 0 |
| B | r2 | 2.54 | 6.05 | 68.59 | 0 |
| C | r2 | 2.86 | 6.72 | 53.65 | 0 |
| A | r2 | 2.82 | 7.79 | 97.04 | 0 |
| C | r3 | 2.89 | 6.67 | 36.85 | 0 |
| A | r3 | 3.06 | 7.13 | 161.32 | 0 |
| B | r3 | 2.70 | 6.06 | 63.78 | 0 |

Fuente por corrida: `results/raw/summary_<ARM>_<RUN_ID>.json`. Orden real de ejecución tal como corrió (Latin square: R1=A→B→C, R2=B→C→A, R3=C→A→B) — ver `results/raw/log_serie_completa.txt` para los timestamps de cada transición.

### Consolidado por brazo (promedio y desviación estándar de las 3 corridas)

| Brazo | p95 medio (ms) | Desviación estándar (ms) | Diferencia vs. B |
|---|---:|---:|---:|
| A | 7.86 | 0.76 | +27% (peor) |
| C | 6.72 | 0.05 | +9% (peor) |
| B | 6.19 | 0.22 | — (referencia, el más rápido) |

**Los tres brazos se diferencian de forma consistente en las 3 corridas, sin excepción: A > C > B en cada una de las 3 repeticiones.** La diferencia C−B (0.53ms) es ~4× mayor que la desviación estándar combinada (~0.14ms) — no es ruido de medición, es una diferencia real y reproducible. Esta es la diferencia central que la sesión del 2026-09-08 no pudo detectar porque medía C tres veces con etiquetas distintas (ver §0).

> **Hit-rate de C**: solo se capturó correctamente para C r3 (**7.6%**, 1668 hits / 20280 misses — `results/raw/cache_C_r3.txt`). El de C r1 y C r2 se perdió: el fix que captura `ha08_cache_hits_total`/`misses_total` en el paso 5 de `run_experiment.sh` se aplicó *mientras la serie ya estaba corriendo* (después de que C r1 y C r2 ya habían terminado su paso 5), y esos contadores viven en el proceso de la API — se reinician en cada recreación de contenedor entre corridas, así que no son recuperables retroactivamente. Es el mismo patrón de pérdida de dato documentado en §3.5 de `EVALUACION_EJECUCION_HA-08.md`, ahora aplicado también a esta repetición. El 7.6% de C r3 es consistente con el 7.1% observado en la sesión inválida del 08-09, lo que sugiere que el patrón de hit-rate bajo no es un artefacto del bug de brazo — es una propiedad real de este diseño de carga (13 min, selección uniforme sobre 10K claves).

### 1.1 Resultados de la sesión del 2026-09-08 (INVÁLIDOS — conservados solo por trazabilidad)

> ⚠️ **Ver §0. Las columnas "A" y "B" de esta tabla son en realidad mediciones del brazo C.** No son evidencia válida para HD-08; se conservan únicamente para que el proceso de detección del bug sea auditable.

| Brazo | Corrida | p50 (ms) | p95 (ms) | Error (%) | Lag proyección p95 aprox. (s) |
|---|---|---:|---:|---:|---:|
| A | r1 | 1.94 | 5.33 | 0 | 0.05 |
| A | r2 | 1.94 | 5.08 | 0 | 0.05 |
| A | r3 | 1.94 | 5.37 | 0 | 0.05 |
| B | r1 | 1.97 | 5.38 | 0 | 0.05 |
| B | r2 | 2.02 | 5.37 | 0 | 0.05 |
| B | r3 | 1.97 | 5.61 | 0 | 0.05 |
| C | r1 | 1.85 | 5.31 | 0 | 0.05 |
| C | r2 | 1.95 | 5.20 | 0 | 0.05 |
| C | r3 | 1.97 | 5.44 | 0 | 0.05 |
| C (TTL=0s) | ttl0 | 1.84 | 5.60 | 0 | 0.05 |
| C (TTL=300s) | ttl300 | 1.92 | 5.27 | 0 | 0.05 |
| C' (coalescencia) | r1 | 2.19 | 4.76 | 0 | 0.05 |

CSV crudo: [`results/consolidado.csv`](results/consolidado.csv) (contiene la mezcla de datos inválidos/válidos por timestamp — usar `results/raw/log_serie_completa.txt` para diferenciar).

---

## 2. Conclusiones

**Basadas en los 9 resultados válidos de §1** (no en la tabla de §1.1, que queda descartada como evidencia).

### 2.1 Sobre la hipótesis HD-08

**Los tres brazos cumplen el umbral de p95 ≤ 150ms con enorme margen** (p95 entre 6.19-7.86ms, es decir, **entre 19× y 24× por debajo del límite**) — pero, a diferencia de la sesión inválida del 08-09, **esta vez los brazos sí se diferencian entre sí de forma clara y reproducible en las 3 repeticiones**, sin excepción: A > C > B.

- **HD-08.1** (A no alcanza el umbral) — **refutada**. A cumple holgadamente (7.86ms vs. 150ms), pero es el más lento de los tres — el costo relativo del modelo normalizado sí es medible (27% más lento que B), solo que no alcanza a comprometer el umbral a este volumen y carga.
- **HD-08.2** (B reduce el p95 ≥60% vs. línea base) — **parcialmente sostenida en dirección, no en magnitud**. B sí es el más rápido de los tres (7.86→6.19ms, -21% vs. A), pero muy por debajo del 60% que planteaba la hipótesis.
- **HD-08.3** (C mejora sobre B) — **refutada, y en la dirección contraria a la esperada**. C es *peor* que B (6.72ms vs. 6.19ms, +9%), no mejor. Lectura mecánica: con el hit-rate real observado (7.6%), la gran mayoría de las peticiones de C ejecutan el trabajo completo de B (proyección) *más* un `GET` a Redis que falla — trabajo estrictamente adicional, no ahorro. El caché no solo no aporta en este régimen de carga, tiene costo neto.
- **HD-08.4** (lag de proyección p95 ≤ 2s) — **aceptada con margen amplio**. Ver §3 para el lag medido en esta serie (mismo orden de magnitud que la sesión anterior, ~0.05s).

### 2.2 Interpretación arquitectónica

**A este volumen (1M registros) y rango de carga (10-80 req/s), ningún brazo está en riesgo de incumplir `EC-LAT-11`** — los tres tienen entre 19× y 24× de margen. Pero, con los brazos correctamente diferenciados, la arquitectura CQRS con caché (C) **no se justifica frente a la proyección materializada sin caché (B)** en este punto de sensibilidad: agrega complejidad operativa (Redis, invalidación, TTL) a cambio de una degradación medible, no de una mejora. La recomendación para este punto de sensibilidad específico es **B** (proyección materializada), no C — el caché solo tendría sentido si el hit-rate real fuera sustancialmente más alto que el 7.6% observado, o si el costo de la consulta base (sin caché) fuera mayor al medido aquí.

Esto no invalida la arquitectura CQRS de Solventa en general (sigue siendo relevante para otros ASR como escalabilidad de escritura o aislamiento de carga), pero sí acota su justificación para *este* punto de sensibilidad a la separación de modelos de lectura (B), sin el paso adicional de caché (C).

### 2.3 Hit-rate real observado, muy por debajo del supuesto de diseño

El hit-rate medido en C r3 fue **7.6%** (1668/21948, ver nota en §1), consistente con el 7.1% de la sesión inválida del 08-09 — confirma que el patrón de hit-rate bajo **no era un artefacto del bug de brazo**, es una propiedad real de este diseño de carga: cada corrida dura 13 minutos con selección uniforme sobre las 10.000 claves del *hot set*, insuficiente para calentar la caché dado el TTL de 30s. Este hit-rate bajo es precisamente la causa mecánica de que C resulte más lento que B en §2.1 — no es una casualidad estadística, es la explicación del hallazgo.

### 2.3bis Sensibilidad a TTL (n=3 por valor, repetido tras el hallazgo §3.7 de la evaluación externa)

Se repitió el punto de sensibilidad 2 del diseño (TTL=0s vs. TTL=300s, brazo C, n=3 cada uno) con el script corregido. Las 6 corridas cerraron con 0% de error:

| TTL | Corrida | p95 (ms) | max (ms) | Hit-rate |
|---|---|---:|---:|---:|
| 0s | r1 | 6.02 | 135.3 | 0.0% |
| 0s | r2 | 6.33 | 162.3 | 0.0% |
| 0s | r3 | 6.27 | 198.1 | 0.0% |
| 300s | r1 | 6.40 | 836.1 | 24.1% |
| 300s | r2 | 6.45 | 135.7 | 33.3% |
| 300s | r3 | 6.57 | 155.2 | 32.3% |

**Promedio: TTL=0 → 6.21ms (σ=0.16) — TTL=300 → 6.47ms (σ=0.09) — diferencia de 0.27ms.**

Dos hallazgos, ambos consistentes con §2.1:

1. **El hit-rate con TTL=300 (24-33%) es sustancialmente más alto que con TTL=30 del protocolo formal (7.6%)** — coherente: un TTL 10× más largo retiene las entradas más tiempo dentro de una corrida de 13 minutos, dando más oportunidad de acierto sobre el *hot set* de 10K claves.
2. **A pesar del hit-rate más alto, TTL=300 es *más lento* que TTL=0, no más rápido** (6.47ms vs. 6.21ms). Esto es contraintuitivo si se esperara que "más hits = más rápido", pero es exactamente la misma mecánica de §2.1: cada hit ahorra la consulta a Postgres, pero cada miss (que sigue siendo mayoría, 67-76%) paga el costo *adicional* del `GET` a Redis que falla, encima del trabajo de B. Con un hit-rate que nunca supera el ~33%, el costo agregado de los misses supera el ahorro de los hits.

**Conclusión:** ni siquiera subiendo el TTL 10× (de 30s a 300s) el caché alcanza a compensar su propio costo estructural en este régimen de carga — refuerza la recomendación de §2.2 de preferir B sobre C para este punto de sensibilidad.

Evidencia: `results/raw/{summary,cache,lag,stats}_C_ttl{0,300}_r{1,2,3}.{json,txt,csv}`.

> **Nota de proceso:** la primera ejecución de esta serie (2026-09-10, madrugada) sufrió contención real de otro contenedor Docker de un proyecto distinto corriendo en la misma máquina (`202620-misw4412-api-empresarial-api-1`, load average 4.74-5.87) — 4 de las 6 corridas mostraron un outlier extremo en `max` (~924 segundos) sin afectar el p95 ni el error rate. Se detuvo ese contenedor y se repitieron únicamente las 4 corridas afectadas (`ttl0_r2`, `ttl0_r3`, `ttl300_r2`, `ttl300_r3`); los valores de la tabla arriba son los de la repetición limpia. Es el mismo patrón de amenaza a la validez documentado en §2.5 para la sesión anterior, esta vez causado por un contenedor distinto (no Kubernetes, que ya se había resuelto).

### 2.4 Punto de quiebre no alcanzado (confirmado también a 150/300/600 req/s)

> ⚠️ **Ver §0.** `run_experiment_alta_carga.sh` tiene el mismo defecto que invalidó el protocolo formal — las 3 filas de la tabla siguiente probablemente midieron todas el brazo C. Pendiente de repetir.

El punto de sensibilidad 3 del diseño (localizar dónde cada brazo deja de cumplir el umbral subiendo la tasa de llegada) **no se pudo observar** dentro del rango de carga del protocolo formal (10→80 req/s): ningún brazo mostró degradación hacia el límite de 150ms en ese rango.

Se ejecutó una iteración adicional de alta carga (`scripts/run_experiment_alta_carga.sh`, `load/k6/read_estado_alta_carga.js`) con escalones de **150 → 300 → 600 req/s** (3 min cada uno, tras 1 min de warm-up descartado) para los tres brazos, buscando específicamente el punto de quiebre. Resultado:

| Brazo | p50 (ms) | p95 (ms) | max (ms) | Error (%) | Throughput real sostenido | CPU `ha08-api` (docker stats final) | Lag proyección (≤0.05s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 1.07 | 2.51 | 576.4 | 0 | ✅ 600 req/s | 16.8% de 1 core | 99.6% |
| B | 1.08 | 2.40 | 278.3 | 0 | ✅ 600 req/s | 0.7% de 1 core | 99.6% |
| C | 1.10 | 2.54 | 994.7 | 0 | ✅ 600 req/s | 0.7% de 1 core | 99.5% |

Incluso a **7.5× la tasa máxima del protocolo formal**, los tres brazos sostuvieron la tasa de arribo objetivo sin errores y con p95 de 2.4–2.5ms — **~60× por debajo** del umbral de 150ms, y sin diferenciación significativa entre brazos. El hit-rate del brazo C sí subió notablemente frente al protocolo formal (**34.0%**, 43238/(43238+84081) acumulado — contra 7.1% en las corridas de 13 min a baja carga), consistente con que a mayor tasa de llegada el *hot set* de 10K claves se "calienta" más rápido dentro de la ventana de TTL=30s; aun así, esa diferencia de hit-rate no se tradujo en diferencia de p95 observable.

**Interpretación:** el cuello de botella no está en la ruta de lectura HTTP→API→Postgres/Redis en este dataset (1M filas, índices efectivos) ni en el pool de conexiones (`DB_POOL_MAX=10`, nunca saturado — CPU de `ha08-api` cayó de 16.8% en A a 0.7% en B/C, coherente con que A sí toca Postgres en cada request mientras B/C lo evitan la mayoría de las veces). El punto de quiebre real está por **encima de 600 req/s** en este montaje, o requeriría un dataset/joins más pesados, o un pool deliberadamente más pequeño para forzar contención — no se intentó llegar más alto por el costo de tiempo de correr escalones aún mayores sin garantía de encontrar el quiebre antes de agotar la capacidad de generación de carga de esta máquina (single-host k6).

Evidencia: `results/raw/{summary,stats,lag}_{A,B,C}_alta_carga.{json,csv,txt}`, `results/raw/log_alta_carga_{A,B,C}.txt`.

### 2.5 Amenazas a la validez específicas de esta ejecución

Además de las ya documentadas en el Anexo D del diseño (montaje local, sin latencia de red entre componentes, etc.), esta corrida concreta introdujo una amenaza adicional:

- **Contención del host por procesos ajenos al experimento.** Durante las corridas de sensibilidad a TTL se detectó un desfase creciente entre el tiempo de reloj y el tiempo de escenario de k6 (hasta 2.6× más lento en la corrida `ttl300`), coincidente con un clúster de Kubernetes de Docker Desktop y otro proyecto (`202620-misw4412-grupo43-api-1`) corriendo en paralelo en la misma máquina. Se detectaron *outliers* de latencia extrema crecientes (70s → 83s → 186s → 151s) en las corridas consecutivas de esa ventana. Tras desactivar Kubernetes, el desfase desapareció (la corrida C' se ejecutó sin desfase, con el *outlier* más bajo de toda la sesión). **El p95 nunca se vio comprometido por esta contención** — solo la cola extrema (max) — pero se documenta como limitación del montaje, no del sistema bajo prueba.
- **Dataset con incidente de duplicación corregido antes de medir.** La primera generación del dataset arrastró filas residuales de una sesión anterior (duplicados exactos ×2 en `hito`/`documento`/`peritaje`). Se detectó, se truncaron las tablas y se regeneró limpio antes de cualquier medición — no afecta los resultados reportados, pero se documenta por transparencia del proceso.
- **`p99` no disponible.** La configuración de k6 usada no expuso `p(99)` en el resumen exportado (solo `p(90)` y `p(95)`); el criterio de aceptación del diseño se basa en p95, por lo que esto no invalida la evaluación, pero limita el detalle solicitado por la plantilla del Anexo C.
- **3 bugs de implementación corregidos durante la ejecución** (no son amenazas a la validez de los datos ya reportados, porque se corrigieron *antes* de que las corridas correspondientes se ejecutaran formalmente):
  1. Import por valor de `pool`/`redis_client` en los brazos A/B/C — rompía toda consulta con `AttributeError`.
  2. El proyector pasaba un string ISO 8601 donde asyncpg esperaba un `datetime` nativo — rompía toda proyección.
  3. `arm_c.py` no manejaba `TTL <= 0`, y Redis rechaza `EX=0` — rompía específicamente la variante de sensibilidad TTL=0.

---

## 3. Verificaciones de sanidad (checklist de la guía técnica)

| Verificación | Resultado |
|---|---|
| `dropped_iterations` = 0 o despreciable en las 12 corridas | ✅ 0 en las 9 corridas principales, TTL=0 y C'; **no verificado aún** en R3 (`dropped_iterations: 3` y `14` reportados en R3/C y R3/B — ver §2.5) |
| Ningún contenedor de infraestructura al 100% de su límite de CPU | ✅ verificado en reposo (<2.3% todos); no monitoreado en tiempo real durante cada corrida |
| `ha08_events_projected_total` creció de forma sostenida (simulador activo) | ✅ confirmado al menos una vez (888 eventos tras el fix inicial) — pendiente extraer el valor final por corrida |
| Tasa de error < 1% | ✅ 0% en las 12 corridas |
| Verificación de paridad de payload (A=B=C) | ✅ pasó formalmente (`verify_parity.sh`) antes de cada corrida |
| Tamaño de la base > `shared_buffers + effective_cache_size` | ✅ 1.376 MB > 768 MB, verificado antes de la primera corrida |

> **Limitación conocida — CPU/memoria por contenedor no es recuperable retroactivamente.** `run_experiment.sh` captura `docker stats --no-stream` al final de cada corrida (`results/raw/stats_*.csv`), pero esa herramienta solo lee el estado *en ese instante*: no existe una fuente donde consultar el uso de CPU/memoria por contenedor de una corrida ya finalizada si no se guardó en su momento. El `docker-compose.yml` de este experimento **no incluye cAdvisor ni node-exporter** (los exportadores estándar de métricas de contenedor hacia Prometheus), así que Prometheus tampoco tiene ese dato histórico. Lo único que Prometheus sí conserva con retención de 7 días es el consumo del **proceso** (no del contenedor completo) de la API y del proyector, vía `process_cpu_seconds_total` y `process_resident_memory_bytes` — expuesto automáticamente por `prometheus-client` en `/metrics`. Es una aproximación parcial (excluye Postgres, Redis, Redpanda y el propio uso de memoria de Docker/overhead del contenedor), pero permite reconstruir al menos la tendencia de CPU/memoria del proceso Python durante una ventana pasada. Ver panel sugerido en §4.4.

---

## 4. Evidencia

### 4.1 Evidencia ya capturada automáticamente

Ubicación: `results/raw/` y `results/evidencia/`.

| Archivo | Contenido | Cómo se generó |
|---|---|---|
| `results/consolidado.csv` | Tabla consolidada de las 12 corridas | `./scripts/collect_results.sh > results/consolidado.csv` |
| `results/raw/summary_<ARM>_<RUN_ID>.json` (×12) | p50/p95/p99, error rate, thresholds, checks — export nativo de k6 | Automático, parte de `run_experiment.sh` |
| `results/raw/stats_<ARM>_<RUN_ID>.csv` (×11) | CPU/memoria por contenedor al final de cada corrida | Automático, parte de `run_experiment.sh` (`docker stats --no-stream`) |
| `results/raw/lag_<ARM>_<RUN_ID>.txt` (×12) | Métrica cruda de lag de proyección (histograma Prometheus) | Automático, parte de `run_experiment.sh` (`curl localhost:8001/metrics`) |
| `results/evidencia/verify_parity_*.log` | Log de la verificación formal de paridad | `./scripts/verify_parity.sh \| tee results/evidencia/...` |
| `results/evidencia/parity_A/B/C.json` | Los 3 payloads comparados byte a byte | Copiados de `/tmp/parity_*.json` tras `verify_parity.sh` |
| `results/evidencia/tamano_dataset.txt` | Conteo de filas y tamaño de BD | Query SQL directa (ver §4.3) |
| `results/evidencia/smoke_test_summary.json` | Prueba de humo previa a las 12 corridas | k6 con `load/k6/smoke_test.js` |

### 4.2 Evidencia pendiente por capturar (espacios a llenar)

> Pega aquí las capturas/archivos cuando los tomes. Cada fila indica dónde debería vivir el archivo dentro del repo.

| Evidencia | Ruta destino sugerida | ¿Automatizable? |
|---|---|---|
| Dashboard de Grafana por corrida y brazo (R1/R2/R3 × A/B/C) | `results/evidencia/r{1,2,3}-{a,b,c}.png` | Manual — ✅ capturado, ver tabla abajo |
| JSON del dashboard de Grafana (para reproducirlo) | [`observability/grafana/provisioning/dashboards/ha08-dashboard.json`](observability/grafana/provisioning/dashboards/ha08-dashboard.json) | ✅ capturado — ver §4.5 |
| Export del volumen de Prometheus (datos crudos, para compartir con el equipo) | *(fuera del repo — pesado; compartir aparte)* | Sí — ver §4.6 |
| Captura de `docker stats` en vivo durante una corrida de alta carga | `results/evidencia/docker_stats_carga_alta.png` o `.txt` | Sí — ver §4.3 |
| Hit-rate exacto del brazo C (no solo el estimado por hits/misses acumulados) | `results/evidencia/hit_rate_brazo_c.txt` | Sí — ver §4.3 |

**Capturas del dashboard de Grafana, una por combinación corrida × brazo** (ventana de tiempo acotada a cada corrida, ver nota sobre el panel "p95 interno por brazo" en §4.4):

| Corrida | Brazo A | Brazo B | Brazo C |
|---|---|---|---|
| R1 | ![R1-A](results/evidencia/r1-a.png) | ![R1-B](results/evidencia/r1-b.png) | ![R1-C](results/evidencia/r1-c.png) |
| R2 | ![R2-A](results/evidencia/r2-a.png) | ![R2-B](results/evidencia/r2-b.png) | ![R2-C](results/evidencia/r2-c.png) |
| R3 | ![R3-A](results/evidencia/r3-a.png) | ![R3-B](results/evidencia/r3-b.png) | ![R3-C](results/evidencia/r3-c.png) |

### 4.3 Cómo capturar automáticamente lo que falta

Comandos listos para correr desde `experiments/ha-08-lectura-siniestro/`:

```bash
# Hit-rate del brazo C (hits / (hits + misses))
curl -s localhost:8000/metrics | grep -E "ha08_cache_(hits|misses)_total" \
  > results/evidencia/hit_rate_brazo_c.txt
cat results/evidencia/hit_rate_brazo_c.txt

# docker stats en vivo (ejecutar DURANTE una corrida, en otra terminal)
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
  > results/evidencia/docker_stats_carga_alta.txt

# Eventos proyectados al final de cada corrida (para el checklist de sanidad)
curl -s localhost:8001/metrics | grep -E "ha08_events_(projected|skipped)_total" \
  > results/evidencia/eventos_proyector_final.txt
```

### 4.4 Cómo capturar los paneles de Grafana (manual, con un paso automatizable)

Datasource: **Prometheus** en `http://prometheus:9090` (nombre del contenedor, no `localhost`).

Queries por panel (pegar en modo "Code" del editor de panel):

| Panel | Query PromQL |
|---|---|
| 1. p95 interno por brazo | `histogram_quantile(0.95, sum(rate(ha08_read_latency_seconds_bucket[1m])) by (le, arm))` |
| 2. Lag de proyección p95 | `histogram_quantile(0.95, rate(ha08_projection_lag_seconds_bucket[1m]))` |
| 3. Hit-rate del caché (brazo C) | `rate(ha08_cache_hits_total[1m]) / (rate(ha08_cache_hits_total[1m]) + rate(ha08_cache_misses_total[1m]))` |
| 4. p95 extremo a extremo (k6) | `k6_ha08_estado_duration_p95` |
| 5. CPU del proceso (API + proyector) — ver limitación en §3 | `rate(process_cpu_seconds_total[1m])` |
| 5b. Memoria residente del proceso (API + proyector) | `process_resident_memory_bytes` |

El panel 5/5b usa `process_cpu_seconds_total` (contador acumulado de segundos de CPU — se grafica con `rate()` para ver la tasa de uso) y `process_resident_memory_bytes` (gauge directo, en bytes). Ambas ya diferencian por `job` (`api` o `projector`) sin necesitar agrupación adicional. Recuerda que esto mide el **proceso Python**, no el contenedor completo — no incluye Postgres/Redis/Redpanda ni el overhead del propio contenedor Docker.

> **Limitación conocida — el panel 1 no se puede filtrar por `run_id`.** `run_id` (r1/r2/r3/ttl0/ttl300) es un concepto que solo existe en `scripts/run_experiment.sh` como sufijo de nombre de archivo (`summary_${ARM}_${RUN_ID}.json`) y como tag de k6 (por eso el panel 4, `k6_ha08_estado_duration_p95`, sí puede filtrarse por `run_id` — k6 lo agrega como label al exportar sus métricas). La métrica interna `ha08_read_latency_seconds` (`api/app/metrics.py`) solo tiene el label `arm`, tomado de `READ_STRATEGY` al arrancar el contenedor (`api/app/main.py:36`); nunca se inyectó `RUN_ID` como variable de entorno ni como labelname del Histogram. Consecuencia práctica: el panel 1 siempre muestra la serie del brazo que esté cargado en el contenedor **en el instante de la query**, sin importar qué corrida fue. Para leerlo correctamente sobre una corrida ya finalizada, no filtres por `run_id` (no existe ese label) — usa el selector de rango de tiempo (arriba a la derecha) para acotar la ventana exacta en que corrió esa corrida; dentro de esa ventana, el label `arm` sí es fiable porque cada corrida usa un único brazo. Si se necesitara filtrar por `run_id` directamente en este panel, habría que agregar esa variable a `docker-compose.yml`, `config.py` y `labelnames` del Histogram — cambio no aplicable retroactivamente a las 12 corridas ya ejecutadas, solo a corridas futuras.

Para consultar un rango de tiempo pasado (p. ej. "hace 2 días") en vez de en vivo: cambia el selector de tiempo arriba a la derecha del dashboard (ícono de reloj) a un rango absoluto que cubra esas fechas — Prometheus conserva 7 días de retención.

1. Entra a **http://localhost:3000** (ver guía completa ya compartida en esta conversación: datasource Prometheus en `http://prometheus:9090`, paneles con las queries de p95/lag/hit-rate).
2. Para cada panel armado: clic en el título del panel → **"Share"** → **"Export as image"** (o captura de pantalla nativa del OS: `Cmd+Shift+4` en Mac).
3. Guarda cada imagen en `results/evidencia/` con el nombre sugerido en la tabla de §4.2.

*Parcialmente automatizable*: Grafana tiene una API de renderizado (`/render/d-solo/...`) que permite pedir un PNG de un panel específico por HTTP sin abrir el navegador, pero requiere el plugin `grafana-image-renderer` instalado (no está en el `docker-compose.yml` actual). Si se agrega esa dependencia, se podría automatizar completamente con:
```bash
curl -s "http://localhost:3000/render/d-solo/<dashboard-uid>/<panel-slug>?panelId=<id>&width=1000&height=500" \
  -H "Authorization: Bearer <api-token>" > results/evidencia/panel.png
```
Por ahora, más simple hacerlo manual (2 minutos por panel).

### 4.5 Cómo exportar el dashboard de Grafana como JSON (para que el equipo lo reproduzca)

1. Con el dashboard abierto → ícono de engranaje (⚙️) → **"JSON Model"**.
2. Copia el JSON completo → guárdalo en `observability/grafana/provisioning/dashboards/ha08-dashboard.json` (crear la carpeta si no existe).
3. Cualquiera que levante el `docker-compose.yml` de este experimento puede importarlo en su propia instancia de Grafana (**Dashboards → New → Import**, pegar el JSON) y ver los mismos paneles sobre sus propios datos.

### 4.6 Cómo exportar los datos crudos de Prometheus para compartir con el equipo

```bash
docker run --rm -v solventa-ha08_promdata:/data -v $(pwd)/results/evidencia:/backup \
  alpine tar czf /backup/prometheus-data.tar.gz -C /data .
```

Genera `results/evidencia/prometheus-data.tar.gz` con todo el histórico de métricas (retención configurada: 7 días). **No subir a git** — es pesado (potencialmente cientos de MB); compartir por Drive/similar si el equipo necesita explorar los datos crudos interactivamente. Para restaurarlo en otra máquina:
```bash
docker run --rm -v solventa-ha08_promdata:/data -v $(pwd):/backup \
  alpine tar xzf /backup/prometheus-data.tar.gz -C /data
```

---

## 5. Pendientes antes de considerar el experimento cerrado

- [x] Capturar hit-rate exacto del brazo C — **7.1%** (269 hits / 3791 consultas) acumulado al cierre de la sesión. Muy por debajo del 96% que HD-08.4 consideraba necesario para sostener el umbral; explicable porque cada corrida es de solo 13 min con selección uniforme sobre 10.000 claves del *hot set* y TTL corto — no hay suficiente tiempo de calentamiento. Ver `results/evidencia/hit_rate_brazo_c.txt`.
- [x] Capturar eventos proyectados/descartados — **5134 proyectados, 21 descartados por versión** (acumulado de toda la sesión, no por corrida individual). Ver `results/evidencia/eventos_proyector_final.txt`.
- [x] Capturar el dashboard de Grafana por corrida y brazo — 9 imágenes (`results/evidencia/r{1,2,3}-{a,b,c}.png`), ver tabla en §4.2.
- [x] Exportar el dashboard de Grafana como JSON reproducible — `observability/grafana/provisioning/dashboards/ha08-dashboard.json` (6 paneles, uid `ffxlg3f0y1qtcc`), ver §4.5.
- [x] Detectado y corregido el defecto que invalidaba las 12 corridas del protocolo formal + las 3 de alta carga: `verify_parity.sh` dejaba la API en el brazo C antes de que k6 midiera (ver §0). Corrección validada con corrida de humo real (`results/raw/summary_A_smoke_fix.json`, `/health` → `A`, contadores de caché en 0/0).
- [x] Repetir las 9 corridas contrabalanceadas A/B/C con el script corregido — completadas sin ninguna aserción fallida (2026-09-09/10). **A > C > B en las 3 repeticiones, sin excepción** (ver §1/§2.1). Hit-rate de C solo capturado para r3 (7.6%) — el de r1/r2 se perdió porque el fix de captura llegó después de que esas corridas ya habían pasado su paso 5 (ver nota en §1).
- [x] Repetir las variantes de sensibilidad TTL con n=3 cada una — completadas sin errores (ver §2.3bis). TTL=0 avg=6.21ms, TTL=300 avg=6.47ms — TTL=300 es *más lento* a pesar de mayor hit-rate (24-33% vs. 0%), mismo patrón de §2.1. 4 de 6 corridas se repitieron por contención de un contenedor externo (documentado en la nota de proceso de §2.3bis).
- [ ] Repetir la iteración de carga alta (150/300/600 req/s) para los 3 brazos con el script corregido
- [ ] Extraer p95 por escalón y segregado caliente/frío desde Prometheus (instrumentación ya lista en `read_estado.js`, ver §0 para las queries PromQL)
- [ ] Exportar volumen de Prometheus si el equipo necesita explorar datos crudos (§4.6)
- [ ] Trasladar estas conclusiones al informe final del curso, con el formato de los Anexos B/C/D de `Diseno_Experimento_HA-08.md`
