# Estado de ejecución — Experimento HA-01

_Actualizado automáticamente: 2026-09-10 21:34:24. Se regenera al cerrar cada corrida y se sube al repositorio con su evidencia._

## Resumen

| | |
| --- | --- |
| Campaña | 2026-09-10 21:34:15  montaje verificado: Docker y API responden |
| Progreso | **11 de 37** corridas ejecutadas · 11 válidas |
| En curso | — |
| Pendientes | 26 · fin estimado hacia las 00:56 |
| Válidas / sospechosas / inválidas / fallidas | 11 / 0 / 0 / 0 |

**Umbral del servicio:** p95 ≤ 225 ms y p99 ≤ 475 ms (250/500 extremo a extremo menos 25 ms de borde, Anexo G). `> 475 ms` es la fracción EXACTA de cotizaciones sobre el umbral del p99, por conteo de buckets: el ASR permite como máximo el 1 %.

Las métricas de cada fila corresponden a la **fase degradada** (proveedor en el estado indicado); en el bloque 4, al escalón de 200 sol/s.

## Bloque 3 — interruptor, recuperación y estampida

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `cache_opportunistic_b3_rate_alto` | C | sin_respuesta | 0.96 | 200 | ✅ válida | 64,3 | 64,9 | 0,00 % | 3,83 % | — | 10/09 17:39 |
| 2 | `cache_opportunistic_b3_rate_bajo` | C | sin_respuesta | 0.96 | 10 | ✅ válida | 64,4 | 65,0 | 0,00 % | 3,44 % | — | 10/09 17:46 |
| 3 | `cache_opportunistic_b3_count_alto` | C | sin_respuesta | 0.96 | 200 | ✅ válida | 64,3 | 64,9 | 0,00 % | 4,22 % | — | 10/09 17:53 |
| 4 | `cache_opportunistic_b3_count_bajo` | C | sin_respuesta | 0.96 | 10 | ✅ válida | 64,4 | 178,1 | 0,00 % | 4,29 % | — | 10/09 18:01 |
| 5 | `cache_opportunistic_b3_estampida_hr0.96` | C | sin_respuesta | 0.96 | 200 | ✅ válida | 64,3 | 64,9 | 0,00 % | 3,88 % | — | 10/09 18:08 |
| 6 | `cache_singleflight_b3_estampida_hr0.96` | C' | sin_respuesta | 0.96 | 200 | ✅ válida | 64,3 | 64,9 | 0,00 % | 4,16 % | — | 10/09 18:15 |
| 7 | `cache_opportunistic_b3_estampida_hr0.50` | C | sin_respuesta | 0.50 | 200 | ✅ válida | 64,6 | 183,3 | 0,00 % | 48,90 % | — | 10/09 18:22 |
| 8 | `cache_singleflight_b3_estampida_hr0.50` | C' | sin_respuesta | 0.50 | 200 | ✅ válida | 64,7 | 183,6 | 0,00 % | 49,42 % | — | 10/09 18:29 |

## Bloque 1 — estrategia contra estado del proveedor (1 repetición)

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 9 | `direct_b1_r1_lento` | A | lento | 0.96 | 100 | ✅ válida | 545,4 | 654,9 | 34,10 % | 0,00 % | — | 10/09 20:17 |
| 10 | `cache_blocking_b1_r1_lento` | B | lento | 0.96 | 100 | ✅ válida | 64,8 | 492,5 | 1,28 % | 0,00 % | — | 10/09 20:24 |
| 11 | `cache_opportunistic_b1_r1_lento` | C | lento | 0.96 | 100 | ✅ válida | 64,8 | 186,0 | 0,00 % | 3,73 % | — | 10/09 20:31 |
| 14 | `direct_b1_r1_sano` | A | sano | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 15 | `cache_blocking_b1_r1_sano` | B | sano | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 16 | `cache_opportunistic_b1_r1_sano` | C | sano | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 17 | `direct_b1_r1_degradado` | A | degradado | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 18 | `cache_blocking_b1_r1_degradado` | B | degradado | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 19 | `cache_opportunistic_b1_r1_degradado` | C | degradado | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 20 | `direct_b1_r1_sin_respuesta` | A | sin_respuesta | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 21 | `cache_blocking_b1_r1_sin_respuesta` | B | sin_respuesta | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 22 | `cache_opportunistic_b1_r1_sin_respuesta` | C | sin_respuesta | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 23 | `direct_b1_r1_caido` | A | caido | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 24 | `cache_blocking_b1_r1_caido` | B | caido | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 25 | `cache_opportunistic_b1_r1_caido` | C | caido | 0.96 | 100 | · pendiente | — | — | — | — | — |  |

## Réplicas de la celda cercana al umbral (B, proveedor lento)

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 12 | `cache_blocking_b1_r2_lento` | B | lento | 0.96 | 100 | · pendiente | — | — | — | — | — |  |
| 13 | `cache_blocking_b1_r3_lento` | B | lento | 0.96 | 100 | · pendiente | — | — | — | — | — |  |

## Bloque 2 — sensibilidad a la tasa de acierto, proveedor lento

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 26 | `cache_blocking_b2_r1_hr0.99` | B | lento | 0.99 | 100 | · pendiente | — | — | — | — | — |  |
| 27 | `cache_blocking_b2_r1_hr0.98` | B | lento | 0.98 | 100 | · pendiente | — | — | — | — | — |  |
| 28 | `cache_blocking_b2_r1_hr0.90` | B | lento | 0.90 | 100 | · pendiente | — | — | — | — | — |  |
| 29 | `cache_blocking_b2_r1_hr0.50` | B | lento | 0.50 | 100 | · pendiente | — | — | — | — | — |  |
| 30 | `cache_opportunistic_b2_r1_hr0.90` | C | lento | 0.90 | 100 | · pendiente | — | — | — | — | — |  |
| 31 | `cache_opportunistic_b2_r1_hr0.50` | C | lento | 0.50 | 100 | · pendiente | — | — | — | — | — |  |

## HD-01.7 — estampida sobre pocas claves (C contra C')

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 32 | `cache_opportunistic_b3_estampida_ttl2` | C | sin_respuesta | 1.0 (20 claves) | 200 | · pendiente | — | — | — | — | — |  |
| 33 | `cache_singleflight_b3_estampida_ttl2` | C' | sin_respuesta | 1.0 (20 claves) | 200 | · pendiente | — | — | — | — | — |  |

## Bloque 4 — latencia contra tasa de llegada

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 34 | `cache_blocking_b4_sano` | B | sano | 0.96 | 20→200 | · pendiente | — | — | — | — | — |  |
| 35 | `cache_opportunistic_b4_sano` | C | sano | 0.96 | 20→200 | · pendiente | — | — | — | — | — |  |
| 36 | `cache_blocking_b4_degradado` | B | degradado | 0.96 | 20→200 | · pendiente | — | — | — | — | — |  |
| 37 | `cache_opportunistic_b4_degradado` | C | degradado | 0.96 | 20→200 | · pendiente | — | — | — | — | — |  |

## Leyenda

- **✅ válida** — pasó las nueve verificaciones de sanidad (tráfico en cada fase, acierto en tolerancia, sin iteraciones descartadas, sin fugas, sin evicción, error < 1 %).
- **⚠️ válida, sospechosa** — válida, pero el detector de interferencia vio el bucle de eventos de la API retrasado (p99 > 50 ms o algún parón > 250 ms). Su cola de latencia puede estar contaminada; el informe debe discutirla.
- **❌ inválida / fallida** — no pasó las verificaciones o no terminó; queda en `results/corridas_fallidas.txt` para repetirla.
- **—** en el lag: corrida anterior a la sonda del detector.

## Dónde está la evidencia

- `results/raw/<corrida>/` — evidencia cruda (métricas finales, configuración efectiva `api_info.json`, verificaciones `sanidad.txt`, resumen de k6), resultados por fase (`fases_resultado.json`) y **series temporales segundo a segundo** (`series.csv`), que no dependen de Prometheus.
- `results/analysis/` — CSV consolidado y figuras del informe.
- Desviaciones respecto del diseño publicado: `README.md`, sección *Desviaciones*.
