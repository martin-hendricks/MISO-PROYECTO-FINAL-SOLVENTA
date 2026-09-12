# Auditoría del experimento HA-08

**Caso de estudio:** Solventa — plataforma insurtech
**Maestría en Ingeniería de Software — MISW4501 Arquitectura de Software**
**Fecha:** 2026-09-12

Contraste entre `Diseno_Experimento_HA-08.md`, `Guia_Tecnica_HA-08.md`, `Informe_Resultados_HA-08_v2.md` y `Hoja-de-trabajo-semana-5.md` (wiki) frente a la implementación y la evidencia cruda de `experiments/ha-08-lectura-siniestro/` en el commit `75af914`.

**Alcance de la verificación.** Se recalcularon las cifras publicadas a partir de los archivos versionados en `results/raw/` (26 `summary_*.json`, 27 `lag_*.txt`, 27 `stats_*.csv`, 14 `cache_*.txt`) y se revisó el código de la API, el proyector, el simulador, los scripts de orquestación y los scripts de carga. **Ninguna corrida fue reejecutada.**

| Resultado | Cantidad |
|---|---|
| Cifras del informe reproducidas sin discrepancia aritmética | **18 / 18** |
| Inconsistencias entre informe, bitácora y archivos versionados | **6** |
| Mediciones que el diseño exige y el informe no entrega | **5** |
| Hallazgos que comprometen el dictamen «A ya cumple el ASR» | **4 críticos + 2 altos** |

---

## 1. Veredicto

**La ejecución es sólida y el informe es honesto.** Cada número de las secciones §3 a §6 coincide con los datos crudos, incluidas medias, desviaciones estándar y porcentajes derivados. La corrección v1→v2 (repetición de `ttl0_r1` y `ttl300_r1` como `r1b`) está bien hecha y bien justificada: el criterio objetivo de corrida limpia —`http_reqs.rate` ≈ 30,8 req/s— es el correcto.

**El problema no está en las cifras: está en lo que se concluye de ellas.** El dictamen central —«A satisface EC-LAT-11 con 19× de margen, luego CQRS no es necesario»— descansa sobre tres condiciones del montaje que abaratan artificialmente el brazo A, sobre un estímulo de carga que no está anclado a ninguna volumetría de negocio, y sobre un perfil de llegada que promedia 31 req/s aunque el informe lo describa como «hasta 80 req/s». La propia Guía Técnica del equipo clasifica un p95 de A por debajo de 20 ms como **síntoma a corregir**, no como resultado a publicar.

**Y hay una brecha de diseño que el dictamen no puede salvar:** el *staleness* visto por el cliente nunca se midió. El Anexo B refuta HD-08 si el umbral se alcanza «a costa de un staleness que haga que el cliente vea un estado desactualizado», y el escenario EC-LAT-11 exige literalmente devolver «el estado **vigente**». Con los datos recogidos ese criterio no es evaluable, así que «C cumple los tres criterios formales» debería decir **«tres de cuatro; el cuarto no se midió»**.

---

## 2. Reproducción de las cifras publicadas

Cada afirmación numérica del informe v2, recalculada desde el archivo crudo que la respalda. La única fila que no coincide es la que motiva el hallazgo E1.

| # | Afirmación del informe | Fuente cruda | Recalculado | |
|---|---|---|---|---|
| 1 | §3 · p95 y p50 de las 9 corridas contrabalanceadas | `summary_{A,B,C}_r{1,2,3}.json` → `ha08_estado_duration` | idénticos hasta el centésimo de ms | ✅ |
| 2 | §3 · p95 medio y σ por brazo: 7,86/0,76 · 6,19/0,22 · 6,72/0,05 | recálculo sobre las 9 corridas | 7,860/0,762 · 6,186/0,225 · 6,719/0,051 | ✅ |
| 3 | §3 · márgenes de 19× / 24× / 22× contra el umbral | 150 ÷ p95 medio | 19,1 · 24,2 · 22,3 | ✅ |
| 4 | §3, §7 · A +27 % y C +9 % sobre B; B −21 % sobre A | recálculo | +27,0 % · +8,6 % · −21,2 % | ✅ |
| 5 | §3 · C−B = 0,53 ms ≈ 4× la desviación combinada | recálculo | 0,533 ms; error estándar de la diferencia 0,130 ms → 4,1× | ✅ |
| 6 | §3 n.4 · hit-rate de C r3 = 7,6 % sobre el 91 % de las peticiones | `cache_C_r3.txt` | 1 668 / 21 948 = 7,60 %; muestra 21 948 / 23 999 = 91,5 % | ✅ |
| 7 | §3 n.2 · lag ≤ 50 ms en ≥ 99,5 % de las observaciones, 9 corridas | `lag_{A,B,C}_r{1,2,3}.txt` | mínimo 99,66 % · máximo 99,87 % | ✅ |
| 8 | §4 · TTL=0 → 6,27 ms (σ 0,06); TTL=300 → 6,50 ms (σ 0,06), con `r1b` | `summary_C_ttl{0,300}_{r1b,r2,r3}.json` | 6,273/0,053 y 6,496/0,066 | ✅ |
| 9 | §4 · la serie de v1 daba σ de 0,16 y 0,09 con las corridas contaminadas | las mismas, con `r1` en vez de `r1b` | 6,204/0,165 y 6,474/0,088 | ✅ |
| 10 | §4 · `http_reqs.rate` de 14,1 y 16,5 req/s contra ~30,8 | `summary_C_ttl{0,300}_r1.json` | 14,078 y 16,518 vs. 30,766–30,770 | ✅ |
| 11 | §4 · hit-rate de TTL=300 en el rango **24–33 %** | `cache_C_ttl300_{r1b,r2,r3}.txt` | 32,9 · 33,3 · 32,3 → **32–33 %** | ❌ **E1** |
| 12 | §5 · p95 por escalón en alta carga (r150 / r300 / r600) | `summary_*_alta_carga_v2.json`, sub-métricas `escalon` | 5,13/4,84/5,24 · 2,63/2,98/2,76 · 2,75/1,50/1,90 | ✅ |
| 13 | §5 · p99 de A: 22,89 ms global, 60,16 ms en r600 | ídem | 22,893 y 60,160 | ✅ |
| 14 | §5 · 136 499 peticiones ≡ integral de las rampas | `http_reqs.count` | 136 499 medidas vs. 136 500 teóricas; el protocolo formal da 24 000 exactas | ✅ |
| 15 | §6 · CPU de Postgres 26,7/67,7 · 10,7/13,4 · 8,1/13,6 | `stats_*_alta_carga_v2.csv`, tramo final | 26,3/67,7 · 10,6/13,4 · 8,0/13,6 (ventana aproximada) | ✅ |
| 16 | §3, §5 · 0 % de error y 0 `dropped_iterations` | `summary` de las 20 corridas válidas | 0 en todas | ✅ |
| 17 | Control de paridad de representación A = B = C | `parity_{A,B,C}.json` | `diff` byte a byte: idénticos | ✅ |
| 18 | Carga de escritura concurrente ~5 eventos/s | `lag_*_r*.txt` → `_count` | 3 826–3 849 eventos en 780 s = 4,91 ev/s | ✅ |

### El resultado principal, a escala

| Brazo | p95 medio (ms) | σ (ms) | % del umbral de 150 ms | Margen |
|---|---:|---:|---:|---:|
| A | 7,86 | 0,76 | 5,2 % | 19,1× |
| B | 6,19 | 0,22 | 4,1 % | 24,2× |
| C | 6,72 | 0,05 | 4,5 % | 22,3× |

El orden A > C > B se repite en las tres corridas y las barras de σ de A y B no se solapan, así que la diferencia es real **en este montaje**. Pero ningún brazo llega al 6 % del umbral, y ese es precisamente el escenario que la Guía Técnica §14 manda diagnosticar antes de publicar (ver V1).

---

## 3. Lo que compromete el dictamen

> Estos hallazgos no dicen que el experimento esté mal ejecutado. Dicen que la frase «A ya cumple el ASR, luego CQRS no es necesario» cubre menos terreno del que aparenta.

### V1 — El propio equipo predijo este resultado y lo clasificó como defecto · CRÍTICO

`Guia_Tecnica_HA-08.md` §14, tabla de solución de problemas, fila uno:

> «p95 del brazo A sospechosamente bajo (< 20 ms) — causa probable: *el dataset cabe en memoria* — acción: verificar el tamaño de la base y **reducir `shared_buffers`**».

A midió **7,86 ms**. La acción prescrita no se ejecutó. La verificación de sanidad que sí se corrió compara el tamaño del *dataset completo* (3 000 MB) contra `shared_buffers + effective_cache_size` (768 MB), lo cual pasa trivialmente y no dice nada sobre el conjunto realmente consultado. En lugar de diagnosticar el síntoma, el resultado se elevó a conclusión principal del informe.

Es lo primero que va a señalar un revisor externo, y es barato de cerrar: bajar `PG_SHARED_BUFFERS` a 32–64 MB y repetir una corrida de A.

### V2 — El estímulo de carga no está anclado a ninguna volumetría · CRÍTICO

`EC-LAT-11` fija el ambiente como «producción en condiciones regulares» sin una sola cifra de caudal, y ni el diseño ni el informe derivan los escalones de 10/25/50/80 req/s de un dato de negocio. El veredicto «A cumple en operación regular» descansa entonces sobre una tasa que nadie ancló, y §5 reconoce que el punto de quiebre no se localizó ni siquiera a 600 req/s de pico — lo que equivale a decir que no se sabe dónde está el margen real.

**Cómo se cierra:** una línea de volumetría en el escenario o en el documento de alcance (siniestros activos × consultas por siniestro por día × factor de pico). Sin ella, cualquier conclusión sobre suficiencia es no falsable.

### V3 — El *hot set* está construido para caber en caché, y además es físicamente contiguo · CRÍTICO

El 80 % del tráfico se dirige a los identificadores 1–10 000, que son exactamente las primeras filas insertadas por `generate_series` en `db/init/03_seed.sql`: ocupan páginas consecutivas en el heap y en los índices. No es sólo que quepan en el caché de página del contenedor — es la disposición física más favorable que puede tener el brazo A. Un conjunto caliente realista está disperso sobre el millón de filas.

El informe §8 reconoce que el hot set «cabe cómodamente en caché», pero no la contigüidad, que es el factor que más abarata los `JOIN` de A.

**Cómo se cierra:** sembrar los identificadores del hot set de forma dispersa (por ejemplo, `id` múltiplos de 100) o desordenar físicamente la tabla, y repetir A.

### V4 — El *staleness* visto por el cliente nunca se midió · CRÍTICO

El Anexo C pide una columna «staleness observado p95» por cada valor de TTL. Lo único medido es el lag del **proyector** (≤ 50 ms), que no es lo mismo: no incluye la ventana durante la cual el caché sirve una entrada anterior. Para TTL=300 el informe escribe «hasta 300 s», que es una cota teórica, no una medición.

Consecuencia: el segundo criterio de refutación del Anexo B —«se refuta si el umbral se alcanza sólo a costa de un staleness que haga que el cliente vea un estado desactualizado»— **no es evaluable con los datos recogidos**, y el escenario EC-LAT-11 exige textualmente devolver «el estado *vigente*».

**Cómo se cierra:** añadir `version` al payload de la proyección y al modelo `EstadoSiniestro`, y comparar en k6 la versión devuelta contra la última publicada. Es un campo, y convierte un riesgo abierto en una métrica.

### V5 — «Hasta 80 req/s» describe un pico instantáneo, no el estímulo aplicado · ALTO

`ramping-arrival-rate` interpola linealmente entre *targets*: lo que el diseño llama «escalones» se ejecutó como rampas.

| Tramo (180 s c/u) | Perfil del Anexo A (mesetas) | Perfil ejecutado (rampas) | Peticiones reales |
|---|---:|---:|---:|
| warm-up (60 s) | 10 req/s | 10 req/s | 600 |
| r10 | 10 req/s | 10 → 10 req/s | 1 800 |
| r25 | 25 req/s | 10 → 25 req/s | 3 150 |
| r50 | 50 req/s | 25 → 50 req/s | 6 750 |
| r80 | 80 req/s | 50 → 80 req/s | 11 700 |
| **Total** | **30 300 peticiones** | **24 000 peticiones** | **24 000 observadas** |

La tasa media real de las nueve corridas es **30,77 req/s** y los 80 req/s se tocan sólo en el último instante. Lo verifiqué por aritmética: la integral de las rampas da 24 000 peticiones exactas, que es el conteo observado; mesetas constantes habrían dado 30 300. Bajo el perfil diseñado, 11 700 de las 24 000 peticiones se habrían servido a 80 req/s sostenidos; bajo el ejecutado, esa cifra es cero.

El informe hace esta aclaración para la iteración de alta carga (§5) pero no para el protocolo formal, donde el resumen ejecutivo depende de ella.

**Cómo se cierra:** reformular a «rampa de 10 a 80 req/s, media 30,8 req/s», o cambiar el ejecutor a `constant-arrival-rate` por escalón si se quiere el perfil que el Anexo A describe.

### V6 — El dataset hace el `JOIN` de A artificialmente barato · ALTO

Todos los siniestros tienen exactamente 5 hitos, 3 documentos y 1 peritaje — varianza cero. El costo que HA-08 postula como origen del problema («componer el estado a partir de cinco entidades normalizadas») nunca llega a materializarse. El informe lo menciona en §8; la observación es que esto no es una nota al pie, es la condición que **produce** el resultado, y debería estar en el resumen ejecutivo junto al dictamen.

### V7 — Verificación positiva que el informe podría reclamar y no reclama

El criterio objetivo de corrida limpia (`http_reqs.rate` ≈ 30,8 req/s) se aplicó sólo a la serie de TTL. Aplicado a todo: las **nueve** corridas del protocolo formal están entre **30,766 y 30,770 req/s**, y las tres de alta carga entre **227,3 y 227,5 req/s**. Ninguna sufrió la contención que afectó a `ttl0_r1` y `ttl300_r1`. Vale la pena decirlo explícitamente en §8, porque refuerza la validez del núcleo del informe.

---

## 4. Inconsistencias entre documentos y evidencia

### E1 — El hit-rate de TTL=300 sigue siendo el de v1 · ALTO

v2 actualizó el p95 de TTL=0 y TTL=300 con las corridas `r1b`, pero dejó la columna de hit-rate en **«24–33 %»**, que incluye el 24,1 % de la corrida descartada. Las tres corridas limpias dan **32,9 / 33,3 / 32,3 %** → **32–33 %**.

La bitácora lo vio y lo escribió —«el hit-rate de `ttl300_r1` … contamina además el límite inferior del rango 24-33 % citado»— y el rango no se corrigió en ninguno de los dos documentos.

Hay una segunda razón, independiente, para no citar ese 24 %: proviene de una muestra de **2 721 de 23 999** peticiones (11 %), la más pequeña de toda la serie.

Corregirlo **refuerza** el argumento de §4 —el hit-rate real (32–33 %) queda más cerca del 44 % teórico de estado estacionario— pero acorta la brecha que sostiene la explicación del régimen transitorio, así que el párrafo hay que reescribirlo, no sólo cambiarle los números.

### E2 — `results/consolidado.csv` está desactualizado · ALTO

El informe §11 lo presenta como «tabla consolidada de las 15+ corridas válidas» y como la pieza que hace las cifras auditables sin reproducir nada. En el commit `75af914` **no contiene `ttl0_r1b` ni `ttl300_r1b`**, y **sí contiene `ttl0_r1` y `ttl300_r1` sin ninguna marca de exclusión**. Es el primer archivo que abriría un revisor, y hoy contradice la tabla de §4.

El glob de `collect_results.sh` (`summary_*_r[0-9]*.json`) sí captura `_r1b`: basta volver a ejecutarlo y añadir una columna de estado.

### E3 — «Tras 1 min de warm-up descartado» no es cierto para el protocolo formal · MEDIO

`load/k6/read_estado.js` etiqueta el warm-up pero **no declara *thresholds* por sub-métrica**, así que `--summary-export` sólo escribe el agregado. Verificado en `summary_A_r1.json`: contiene un único `ha08_estado_duration` con `count = 23 999`, el total de la corrida.

Los p95 publicados incluyen las 600 peticiones de warm-up, que se sirven justo después del `docker compose restart postgres` y son las más lentas de la corrida. El efecto es pequeño (2,5 % de la muestra) y presumiblemente simétrico entre brazos, pero sesga los tres p95 hacia arriba y la frase es incorrecta. En la iteración de alta carga sí está bien excluido.

### E4 — La bitácora conserva las cifras de v1 en la prosa · MEDIO

`INFORME.md` §2.3bis punto 2 y el checklist de §5 siguen diciendo «TTL=0 avg 6,21 ms — TTL=300 avg 6,47 ms», los valores calculados con `r1`, mientras la tabla inmediatamente superior en la misma sección ya dice 6,27 y 6,50. El informe de la wiki usa los nuevos. Como §11 declara la bitácora la fuente de verdad del proceso, la discrepancia importa.

### E5 — El límite de CPU de la API es 2 cores, no 1 · BAJO

`docker-compose.yml` asigna `cpus: "2.0"` al servicio `api`. La frase «`ha08-api` no se acerca a saturar su límite de 1 core» aparece **dos veces en la bitácora** (§2.4, §3) y **una en el informe** (§5). El máximo observado es 46,5 % de un core, es decir ~23 % del límite real: la conclusión no cambia, el dato sí. El límite de Postgres (2 cores) sí está bien citado en §6.

### E6 — El conteo de corridas válidas es inconsistente · BAJO

El checklist de la bitácora dice «18 corridas válidas» en una fila y «15 corridas válidas» en otra; el informe habla de «15+». Con las repeticiones `r1b` el total es **20**: 9 del protocolo formal, 8 de TTL y 3 de alta carga.

---

## 5. Brechas frente al diseño

Todas están declaradas en el informe como pendientes o no disponibles, así que no son omisiones encubiertas. Lo que se aporta aquí es cuánto cuesta cerrar cada una y qué se pierde mientras siga abierta.

| Brecha | Dónde lo exige el diseño | Qué se pierde | Costo |
|---|---|---|---|
| **B1 · El brazo C' nunca se midió válidamente.** Existe `summary_C_PRIME_r1.json` pero es de la sesión invalidada. | Anexo A «factor adicional»; Anexo D lo declara *el control* de la asimetría de serialización | El hallazgo principal sobre C es que su costo está en `orjson.dumps` + `SET`. C' es exactamente el brazo que aislaría esa causa, y falta. | 1 corrida · 13 min |
| **B2 · Staleness observado por TTL.** | Anexo C, tabla de sensibilidad 2; Anexo B, criterio de refutación | Ver V4: el criterio de refutación no es evaluable. | 1 campo + 1 check en k6 |
| **B3 · p95 por escalón en el protocolo formal.** La tabla del Anexo C queda con las cuatro filas en «no disponible». | Anexo C, punto de sensibilidad 3 | No se puede decir si el p95 de 7,86 ms de A viene del tramo de 10 req/s o del de 80. | 3 corridas · ~40 min |
| **B4 · Latencia interna del servicio.** `ha08_read_latency_seconds` está instrumentada y en Grafana, pero no aparece ni un valor en el informe. | Anexo A (variable dependiente); Guía §12 la marca obligatoria | Es la métrica que separa el costo del stack ASGI/HTTP del costo de la estrategia de lectura. Sin ella no se puede sostener que los ~6–8 ms sean arquitectura y no transporte — que es justo lo que decide si la diferencia B vs. C significa algo. | 1 consulta a Prometheus |
| **B5 · p99 en protocolo formal y TTL.** | Anexo C, plantilla de registro | El p99 fue precisamente lo que reveló la degradación de cola de A en alta carga (60 ms en r600). En el rango formal no existe. | 1 línea: `--summary-trend-stats` en el servicio `k6` |

**Matiz sobre B3.** El informe la cataloga como «cerrada, no recuperable». Es cierto que la vía de Prometheus no funciona (se verificó que la métrica no existe como histograma), pero `read_estado.js` **ya** etiqueta cada petición con su escalón: basta copiar el bloque de `thresholds` por sub-métrica de `read_estado_alta_carga.js` y repetir. Son tres corridas, no un rediseño.

---

## 6. Coherencia con la arquitectura de semana 5

Contrastado contra la última versión publicada de las vistas: modelo de componentes, vista de despliegue, vista de información, estilos y tácticas.

### A1 — La arquitectura rechaza el *staleness* sobre el mismo dato que B y C sirven desde una copia · CRÍTICO

`Hoja-de-trabajo-semana-5.md` §1.2.4 justifica la redundancia **pasiva** en siniestros así:

> «poner la réplica a servir lecturas introduciría *staleness* sobre un dato que el cliente lee como el estado vigente de su reclamación, así que se mantiene fuera del tráfico».

Ese argumento descalifica a B y a C, que sirven ese mismo dato desde una copia eventualmente consistente — con una ventana de hasta 300 s en la carrera de invalidación documentada en §4 del informe.

O la arquitectura acepta staleness en el estado de siniestro, y entonces hay que reescribir la justificación de la réplica pasiva; o no lo acepta, y entonces B y C no son opciones y el dictamen «la complejidad mínima suficiente es A» no sólo es correcto: **es el único admisible**, y por una razón que el informe no usa. La tensión no aparece en ninguno de los dos documentos.

### A2 — El modelo de lectura de HA-08 no existe en ninguna vista publicada · ALTO

- El **modelo de componentes** no tiene proyector, proyección ni caché de estado de siniestro. Los componentes de siniestros son `:MsSiniestros (Principal)`, `:DBSiniestros`, `:Sincronizador` y `:DBSiniestros (Replica)`.
- La **vista de información** no tiene entidad de proyección.
- **§2.3 no lista CQRS** entre los estilos arquitectónicos adoptados.
- Las tablas de **tácticas de latencia** (§1.2.1, §2.4) cubren `EC-LAT-09`, `EC-LAT-05/06` y `EC-LAT-03/04`, pero **no `EC-LAT-11`**.

Es decir: el único ASR (A,A) de latencia del dominio de siniestros no tiene tácticas asignadas en ninguna vista; aparece dos veces, como promesa a futuro — «se atiende con un modelo de lectura separado (CQRS), que es precisamente la hipótesis que valida el experimento».

Efecto práctico: el resultado del experimento no obliga a cambiar ningún diagrama, porque ningún diagrama incorporó la hipótesis. Pero el hueco sigue ahí, y ahora hay que cerrarlo con evidencia que dice que CQRS no se justifica por latencia.

### A3 — La ficha del experimento declara una traza de vistas que no existe · MEDIO

La ficha en `Diseno_Experimento_HA-08.md` dice: «Vista funcional (modelo de componentes: API de consulta, *proyector*, almacenes de lectura y escritura); Vista de información (modelo de datos: esquema transaccional vs. proyección); Vista de despliegue». Ninguno de esos elementos está publicado. En la copia de semana 5 (§3.1) ya se recortó «proyector» y quedó «Vista de información ;» vacío — el hueco está detectado pero no resuelto.

El contraste con el experimento HA-01, en el mismo documento, es directo: su ficha incluye una fila **«Correspondencia con el diagrama de componentes»** que verifica pieza por pieza que el montaje no introduce componentes nuevos. HA-08 no la tiene, y la necesita más.

### A4 — Divergencias entre la ficha suelta y la copia de semana 5 · BAJO

La distribución de actividades asigna el proyector y el simulador a un integrante distinto en cada copia, y el esfuerzo total pasa de 60 h (4 × 15 h) a 42 h (4 × 10,5 h) sin nota de recalibración. Cosmético, pero ambos son documentos entregables.

---

## 7. Revisión de la implementación

### Lo que está bien resuelto

- **Ruta de lectura íntegramente asíncrona** (`asyncpg`, `redis.asyncio`), el requisito no negociable del diseño: un driver síncrono habría producido una refutación falsa.
- **La paridad de representación está garantizada por construcción**, no sólo por el check: los tres brazos pasan por `response_model=EstadoSiniestro` y `ORJSONResponse`. El `diff` de `parity_{A,B,C}.json` lo confirma byte a byte.
- **Upsert idempotente por versión** con `WHERE version < EXCLUDED.version`, e invalidación de caché sólo cuando el upsert aplica.
- **Los buckets del histograma incluyen `0.150` explícitamente**, el umbral del ASR — detalle que evita interpolar el p95 entre 0,100 y 0,250.
- **La corrección del defecto de `verify_parity.sh` es correcta y verificable**: la aserción sobre `/health` corta antes de medir, y las 20 corridas válidas la pasaron.
- **Controles del Anexo A respetados**: 2 workers, pool fijo 10/10 idéntico entre brazos, 1 000 000 de siniestros, límites de CPU y memoria por componente, 4,91 ev/s de escritura concurrente.

### Observaciones no recogidas en el informe

- **La carrera de invalidación no es sólo de TTL alto.** `arm_c.py` guarda el payload sin número de versión y el proyector borra por clave: no hay CAS ni `WATCH`. Con TTL=30 la ventana ya es de 30 s sobre el dato más sensible del escenario.
- **El simulador pierde eventos en silencio.** `send_and_wait` no tiene `try/except` y se ejecuta fuera de la transacción. No afecta la latencia medida, pero sí la afirmación de que la proyección está «bajo actualización activa»: no hay contador de eventos *publicados* contra el que contrastar los 5 134 proyectados.
- **La captura de `docker stats` corre desde el host durante la medición**, cada 10 s. Marginal a 31 req/s; medible a 600.
- **El `restart postgres` previo a cada corrida vacía `shared_buffers`**, lo cual es bueno para la comparabilidad — pero conviene declararlo, porque el contrabalanceo del Anexo A se justificaba por un caché que sí se puede limpiar parcialmente.
- **La tasa del simulador es 4,91 ev/s**, no 5: el `sleep` es posterior al trabajo. Conviene reportar el valor medido.

---

## 8. Qué hacer, en orden

Ordenado por relación entre lo que cierra y lo que cuesta. Los tres primeros se hacen **sin volver a correr nada**.

| # | Acción | Cierra | Costo |
|---|---|---|---|
| 1 | Corregir el rango de hit-rate de TTL=300 a 32–33 % y reescribir el párrafo del régimen transitorio; regenerar `consolidado.csv` con columna de estado; corregir «1 core» → «2 cores»; alinear las cifras de la bitácora con las del informe. | E1, E2, E4, E5, E6 | edición |
| 2 | Reformular «hasta 80 req/s» como «rampa de 10 a 80 req/s, media 30,8» en el resumen ejecutivo, y retirar «tras 1 min de warm-up descartado» del protocolo formal. | V5, E3 | edición |
| 3 | Extraer de Prometheus el p95 de `ha08_read_latency_seconds` por brazo y publicarlo junto al p95 de k6. | B4 | 1 consulta |
| 4 | Exponer `version` en la proyección y en `EstadoSiniestro`; añadir en k6 un check de frescura contra la última versión publicada. Repetir la serie de TTL. | V4, B2 — y con ello el criterio de refutación del Anexo B | 6 corridas |
| 5 | Bajar `PG_SHARED_BUFFERS` a 32–64 MB y sembrar el hot set disperso; repetir el brazo A. Es el experimento que la Guía §14 ya prescribía. | V1, V3, V6 — y decide si el dictamen se sostiene | 3 corridas |
| 6 | Añadir `thresholds` por sub-métrica a `read_estado.js` y `--summary-trend-stats` al servicio `k6`; repetir el protocolo formal. Cierra dos tablas completas del Anexo C. | B3, B5 | 9 corridas |
| 7 | Correr C' una vez con el script corregido. | B1 | 1 corrida |
| 8 | Anclar `EC-LAT-11` a una volumetría: siniestros activos × consultas/siniestro/día × factor de pico. Sin esto, ningún resultado de este experimento es falsable. | V2 | decisión de negocio |
| 9 | Resolver en la wiki la contradicción sobre *staleness* del estado de siniestro (§1.2.4 vs. hipótesis HD-08) y asignar tácticas a `EC-LAT-11` en las vistas, cualquiera que sea el dictamen final. | A1, A2, A3 | arquitectura |

---

## Anexo — Trazabilidad de la auditoría

| Artefacto auditado | Ubicación |
|---|---|
| Diseño del experimento | wiki · `files/Diseno_Experimento_HA-08.md` |
| Guía técnica | wiki · `files/Guia_Tecnica_HA-08.md` |
| Informe de resultados v2 | wiki · `files/Informe_Resultados_HA-08_v2.md` |
| Arquitectura (última versión) | wiki · `Hoja-de-trabajo-semana-5.md` |
| Escenario de calidad | wiki · `Escenarios-de-calidad-ajustados-hoja-de-trabajo.md` § EC-LAT-11 |
| Implementación y evidencia | `experiments/ha-08-lectura-siniestro/` @ `75af914` |
| Bitácora técnica | `experiments/ha-08-lectura-siniestro/INFORME.md` |
| Evidencia cruda recalculada | `experiments/ha-08-lectura-siniestro/results/raw/` |
