# Estado de ejecución — Experimento HA-01

_Actualizado automáticamente: 2026-09-11 19:01:03. Se regenera al cerrar cada corrida y se sube al repositorio con su evidencia._

## Resumen

| | |
| --- | --- |
| Campaña | 2026-09-11 18:39:46  BLOQUE x: inicio |
| Progreso | **40 de 52** corridas ejecutadas · 40 válidas |
| En curso | — |
| Pendientes | 12 · fin estimado hacia las 20:40 |
| Válidas / sospechosas / inválidas / fallidas | 35 / 0 / 0 / 0 |

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
| 8 | `cache_singleflight_b3_estampida_hr0.50` | C' | sin_respuesta | 0.50 | 200 | ⚠️ válida, revisar (respaldo por encima del presupuesto) | 64,7 | 183,6 | 0,00 % | 49,42 % | — | 10/09 18:29 |
| 52 | `cache_singleflight_b3_estampida_hr0.50b` | C' | sin_respuesta | 0.96 | 200 | · pendiente | — | — | — | — | — |  |

## Bloque 1 — estrategia contra estado del proveedor (1 repetición)

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 9 | `direct_b1_r1_lento` | A | lento | 0.96 | 100 | ✅ válida | 545,4 | 654,9 | 34,10 % | 0,00 % | — | 10/09 20:17 |
| 10 | `cache_blocking_b1_r1_lento` | B | lento | 0.96 | 100 | ✅ válida | 64,8 | 492,5 | 1,28 % | 0,00 % | — | 10/09 20:24 |
| 11 | `cache_opportunistic_b1_r1_lento` | C | lento | 0.96 | 100 | ✅ válida | 64,8 | 186,0 | 0,00 % | 3,73 % | — | 10/09 20:31 |
| 14 | `direct_b1_r1_sano` | A | sano | 0.96 | 100 | ✅ válida | 174,1 | 208,1 | 0,00 % | 0,00 % | 4,6 | 10/09 21:55 |
| 15 | `cache_blocking_b1_r1_sano` | B | sano | 0.96 | 100 | ✅ válida | 64,9 | 143,9 | 0,00 % | 0,00 % | 4,4 | 10/09 22:02 |
| 16 | `cache_opportunistic_b1_r1_sano` | C | sano | 0.96 | 100 | ✅ válida | 64,9 | 144,7 | 0,00 % | 0,23 % | 4,5 | 10/09 22:09 |
| 17 | `direct_b1_r1_degradado` | A | degradado | 0.96 | 100 | ✅ válida | 122,2 | 778,1 | 4,55 % | 98,94 % | 4,6 | 10/09 22:16 |
| 18 | `cache_blocking_b1_r1_degradado` | B | degradado | 0.96 | 100 | ✅ válida | 64,3 | 64,9 | 0,18 % | 3,43 % | 4,5 | 10/09 22:24 |
| 19 | `cache_opportunistic_b1_r1_degradado` | C | degradado | 0.96 | 100 | ✅ válida | 64,3 | 64,9 | 0,00 % | 4,01 % | 4,0 | 10/09 22:31 |
| 20 | `direct_b1_r1_sin_respuesta` | A | sin_respuesta | 0.96 | 100 | ✅ válida | 64,9 | 776,5 | 4,25 % | 99,43 % | 4,6 | 10/09 22:38 |
| 21 | `cache_blocking_b1_r1_sin_respuesta` | B | sin_respuesta | 0.96 | 100 | ✅ válida | 64,3 | 64,9 | 0,18 % | 3,81 % | 4,2 | 10/09 22:45 |
| 22 | `cache_opportunistic_b1_r1_sin_respuesta` | C | sin_respuesta | 0.96 | 100 | ✅ válida | 64,3 | 64,9 | 0,00 % | 3,82 % | 4,5 | 10/09 22:52 |
| 23 | `direct_b1_r1_caido` | A | caido | 0.96 | 100 | ✅ válida | 64,4 | 80,9 | 0,00 % | 98,89 % | 4,6 | 10/09 22:59 |
| 24 | `cache_blocking_b1_r1_caido` | B | caido | 0.96 | 100 | ✅ válida | 64,3 | 64,9 | 0,00 % | 3,95 % | 4,5 | 10/09 23:06 |
| 25 | `cache_opportunistic_b1_r1_caido` | C | caido | 0.96 | 100 | ✅ válida | 64,3 | 64,9 | 0,00 % | 3,67 % | 4,3 | 10/09 23:13 |

## Réplicas de la celda cercana al umbral (B, proveedor lento)

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 12 | `cache_blocking_b1_r2_lento` | B | lento | 0.96 | 100 | ✅ válida | 64,8 | 485,8 | 1,15 % | 0,00 % | 4,6 | 10/09 21:41 |
| 13 | `cache_blocking_b1_r3_lento` | B | lento | 0.96 | 100 | ✅ válida | 64,8 | 490,9 | 1,24 % | 0,00 % | 4,7 | 10/09 21:48 |

## Bloque 2 — sensibilidad a la tasa de acierto, proveedor lento

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 26 | `cache_blocking_b2_r1_hr0.99` | B | lento | 0.99 | 100 | ✅ válida | 64,4 | 65,0 | 0,29 % | 0,00 % | 4,4 | 10/09 23:20 |
| 27 | `cache_blocking_b2_r1_hr0.98` | B | lento | 0.98 | 100 | ✅ válida | 64,6 | 452,8 | 0,73 % | 0,00 % | 4,2 | 10/09 23:27 |
| 28 | `cache_blocking_b2_r1_hr0.90` | B | lento | 0.90 | 100 | ✅ válida | 443,3 | 527,6 | 3,06 % | 0,00 % | 4,0 | 10/09 23:34 |
| 29 | `cache_blocking_b2_r1_hr0.50` | B | lento | 0.50 | 100 | ✅ válida | 531,1 | 556,1 | 16,75 % | 0,00 % | 4,5 | 10/09 23:42 |
| 30 | `cache_opportunistic_b2_r1_hr0.90` | C | lento | 0.90 | 100 | ✅ válida | 181,8 | 188,4 | 0,00 % | 9,18 % | 4,0 | 10/09 23:49 |
| 31 | `cache_opportunistic_b2_r1_hr0.50` | C | lento | 0.50 | 100 | ✅ válida | 188,5 | 189,7 | 0,00 % | 49,20 % | 4,4 | 10/09 23:56 |

## HD-01.7 — estampida sobre pocas claves (C contra C')

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 32 | `cache_opportunistic_b3_estampida_ttl2` | C | sin_respuesta | 1.0 | 200 | ✅ válida | 64,5 | 181,4 | 0,00 % | 99,42 % | 4,2 | 11/09 00:03 |
| 33 | `cache_singleflight_b3_estampida_ttl2` | C' | sin_respuesta | 1.0 | 200 | ✅ válida | 64,7 | 184,6 | 0,00 % | 98,50 % | 4,1 | 11/09 00:10 |
| 50 | `cache_opportunistic_b3_estampida_ttl2b` | C | sin_respuesta | 1.0 (20 claves) | 200 | · pendiente | — | — | — | — | — |  |
| 51 | `cache_singleflight_b3_estampida_ttl2b` | C' | sin_respuesta | 1.0 (20 claves) | 200 | · pendiente | — | — | — | — | — |  |

## Bloque 4 — latencia contra tasa de llegada

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 34 | `cache_blocking_b4_sano` | B | sano | 0.96 | 20→200 | ⚠️ válida, revisar (acierto fuera de tolerancia) | 131,4 | 166,0 | 0,00 % | 0,00 % | 4,2 | 11/09 00:20 |
| 35 | `cache_opportunistic_b4_sano` | C | sano | 0.96 | 20→200 | ⚠️ válida, revisar (acierto fuera de tolerancia) | 133,0 | 167,7 | 0,00 % | 0,48 % | 4,0 | 11/09 00:29 |
| 36 | `cache_blocking_b4_degradado` | B | degradado | 0.96 | 20→200 | ⚠️ válida, revisar (acierto fuera de tolerancia) | 64,3 | 64,9 | 0,03 % | 14,74 % | 4,2 | 11/09 00:39 |
| 37 | `cache_opportunistic_b4_degradado` | C | degradado | 0.96 | 20→200 | ⚠️ válida, revisar (acierto fuera de tolerancia) | 64,3 | 64,9 | 0,00 % | 14,78 % | 4,0 | 11/09 00:49 |

## Otras

| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms | > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |
| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 38 | `cache_blocking_b3b_pol_rate_alto` | B | sin_respuesta | 0.96 | 200 | ✅ válida | 64,3 | 64,9 | 0,24 % | 4,32 % | 4,2 | 11/09 18:46 |
| 39 | `cache_blocking_b3b_pol_rate_bajo` | B | sin_respuesta | 0.96 | 10 | ✅ válida | 64,4 | 65,0 | 0,77 % | 3,95 % | 3,2 | 11/09 18:53 |
| 40 | `cache_blocking_b3b_pol_count_alto` | B | sin_respuesta | 0.96 | 200 | ✅ válida | 64,3 | 64,9 | 0,07 % | 3,97 % | 3,7 | 11/09 19:01 |
| 41 | `cache_blocking_b3b_pol_count_bajo` | B | sin_respuesta | 0.96 | 10 | · pendiente | — | — | — | — | — |  |
| 42 | `cache_blocking_b5_intermitente_rate` | B | intermitente | 0.96 | 200 | · pendiente | — | — | — | — | — |  |
| 43 | `cache_opportunistic_b5_intermitente_rate` | C | intermitente | 0.96 | 200 | · pendiente | — | — | — | — | — |  |
| 44 | `cache_blocking_b5_intermitente_count` | B | intermitente | 0.96 | 200 | · pendiente | — | — | — | — | — |  |
| 45 | `cache_opportunistic_b5_intermitente_count` | C | intermitente | 0.96 | 200 | · pendiente | — | — | — | — | — |  |
| 46 | `cache_blocking_b4b_sano` | B | sano | 0.96 | 20→200 | · pendiente | — | — | — | — | — |  |
| 47 | `cache_opportunistic_b4b_sano` | C | sano | 0.96 | 20→200 | · pendiente | — | — | — | — | — |  |
| 48 | `cache_blocking_b4b_degradado` | B | degradado | 0.96 | 20→200 | · pendiente | — | — | — | — | — |  |
| 49 | `cache_opportunistic_b4b_degradado` | C | degradado | 0.96 | 20→200 | · pendiente | — | — | — | — | — |  |

## Leyenda

- **✅ válida** — pasó las nueve verificaciones de sanidad (tráfico en cada fase, acierto en tolerancia, sin iteraciones descartadas, sin fugas, sin evicción, error < 1 %).
- **⚠️ válida, revisar** — pasó las verificaciones, pero algo pide una segunda lectura antes de citarla en el informe:
  - *interferencia*: el bucle de eventos de la API estuvo retrasado (p99 > 50 ms o algún parón > 250 ms), así que su cola de latencia puede estar contaminada.
  - *acierto fuera de tolerancia*: alguna fase se desvió más de 2 puntos del objetivo. Las verificaciones lo miran de forma acumulada; esto lo mira fase a fase.
  - *respaldo por encima del presupuesto*: en C o C' el respaldo superó 230 ms, que es presupuesto + tarifa + margen. En B no aplica, porque allí el respaldo espera al proveedor hasta el timeout duro.
- **❌ inválida / fallida** — no pasó las verificaciones o no terminó; queda en `results/corridas_fallidas.txt` para repetirla.
- **—** en el lag: corrida anterior a la sonda del detector.

## Dónde está la evidencia

- `results/raw/<corrida>/` — evidencia cruda (métricas finales, configuración efectiva `api_info.json`, verificaciones `sanidad.txt`, resumen de k6), resultados por fase (`fases_resultado.json`) y **series temporales segundo a segundo** (`series.csv`), que no dependen de Prometheus.
- `results/analysis/` — CSV consolidado y figuras del informe.
- Desviaciones respecto del diseño publicado: `README.md`, sección *Desviaciones*.
