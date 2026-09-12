# Evaluación del experimento HA-01 — versión corregida

_Sustituye a la evaluación del 10/09/2026 (redactada con 15 de 37 corridas). Cerrada
el 12/09/2026 con **52 corridas, todas válidas**. Cada cifra de este documento sale de
`results/analysis/resultados_por_fase.csv` y de la carpeta de cada corrida; ninguna se
cita de memoria._

## 1. Veredicto

La hipótesis HD-01 **se confirma, y con un matiz que el diseño no anticipaba**: el
desacople no es necesario frente a cualquier proveedor degradado, sino frente al
proveedor que **falla a medias** —lento pero vivo, o intermitente—. Cuando el
proveedor cae del todo, el interruptor de circuito rescata también a una caché
simple, y el brazo B cumple el ASR.

Esa distinción es el resultado principal del experimento y obliga a reescribir la
respuesta de la wiki a la pregunta 3 del enunciado: hoy atribuye el mérito a la
actualización oportunista sin separar qué hace el interruptor y qué hace el desacople.

## 2. Qué cambia respecto de la evaluación del 10/09

| Observación original | Estado | Corrección |
| --- | --- | --- |
| §4.1 Reformular HD-01.4 | ✅ válida | Con un matiz: la segunda cláusula propuesta es casi una identidad. Ver §4 |
| §4.2 Reubicar el punto de sensibilidad 4 | ✅ válida | Y decisiva: al correr las políticas en B aparece el incumplimiento que en C era invisible |
| §4.3 Falta el estado de fallas intermitentes | ✅ válida · mecanismo corregido | `toxicity` de Toxiproxy se aplica **por conexión, no por petición**: con el pool de conexiones persistentes de httpx la fracción real habría quedado fuera de control. Se implementó en el doble, por petición y por hash del cliente |
| §4.4 `PoolTimeout` como falla del proveedor | ✅ defecto real · sin efecto medido | Corregido. Al separarlo se comprueba que **no se produjo ninguno**: los fallos que abrieron el interruptor eran timeouts auténticos |
| §4.5 Corrida de C′ al 50 % dada por válida | ✅ válida | Repetida con el detector: p99 de 311 → 183 ms, respaldo de 467 → 189 ms, 0 parones del bucle. Era un transitorio del entorno |
| §4.6 El camino frío no cabe en EC-LAT-07 | ❌ **incorrecta** | El adaptador está en **111–117 ms** de p95 y sólo el 2,5–4,1 % de sus llamadas pasa de 120 ms: EC-LAT-07 **se cumple**. Los 155–178 ms citados son la cotización completa, que incluye los 60 ms de tarifa. El sobrecosto medido de Toxiproxy es de ~1 ms, no de 50 |
| §4.7 Replicar A sano y B degradado | ❌ **premisa falsa** | B degradado queda en 0,18 % frente al 1 % permitido: lejos del umbral. A sano ya tenía cuatro medidas (p95 173,3–174,6 ms), porque cada corrida incluye su fase sana |
| §4.7 "A muestra 103 s" | ❌ **unidades mal leídas** | Son 103,77 invocaciones por segundo. Las métricas del interruptor sí aplican a A y B: el interruptor vive en el adaptador, que es común |
| §4.7 El p95 no discrimina | ✅ válida | Con acierto del 96 %, el p95 cae siempre dentro de los aciertos de caché. **El p99 y la fracción sobre 475 ms son las métricas que deciden** |
| §4.8 "Cuatro estados", EC-LAT-09, Jira | ✅ válidas | La incoherencia de los estados está también en la wiki |
| §4.8 56 h frente a 40 h | ❌ **no existe** | Diseño y wiki coinciden: 4 × 14 h = 56 h en 1,5 semanas |
| §6 "edad p50 ≈ 575 s" como hallazgo | ❌ **artefacto** | Esas edades las fija la precarga (pool caliente de 0 a 450 s, pool vencido en TTL + 120 s), no la arquitectura. El resultado que no depende del montaje es la proporción con respaldo |

## 3. Resultados por sub-hipótesis

### HD-01.1 — con el proveedor sano cumplen los tres brazos ✅

p95: **A 174,1 ms · B 64,9 ms · C 64,9 ms**, contra un umbral de 225 ms. Replicado en la
fase sana de todas las corridas (A entre 173,3 y 174,6 ms).

### HD-01.2 — con el proveedor degradado sólo cumple C ⚠️ **se confirma sólo en parte**

Porcentaje de cotizaciones por encima de 475 ms; el ASR permite como máximo el 1 %:

| Estado del proveedor | A | B | C |
| --- | ---: | ---: | ---: |
| sano | 0,00 % | 0,00 % | 0,00 % |
| **lento** | ❌ 34,10 % | ❌ **1,28 %** | ✅ 0,00 % |
| degradado | ❌ 4,55 % | ✅ 0,18 % | ✅ 0,00 % |
| sin respuesta | ❌ 4,25 % | ✅ 0,18 % | ✅ 0,00 % |
| caído | ✅ 0,00 % | ✅ 0,00 % | ✅ 0,00 % |
| **intermitente** (30 % de fallos) | — | ❌ **1,10 %** | ✅ 0,00 % |

**B sólo incumple cuando el proveedor falla a medias.** Con el proveedor caído, el
interruptor abre en segundos y a partir de ahí B también falla rápido: el ASR se
cumple. Con el proveedor lento, el interruptor **nunca abre** —el proveedor responde
dentro del timeout duro— y B paga el camino frío en cada fallo de caché.

### HD-01.3 — el camino degradado es más rápido que el frío ⚠️ **depende del estado**

p95 por camino en el brazo C:

| Estado | caché | camino frío | respaldo |
| --- | ---: | ---: | ---: |
| lento | 64,3 ms | 159,0 ms | **189,3 ms** |
| degradado | 64,2 ms | 139,0 ms | 179,8 ms |
| sin respuesta | 64,2 ms | 172,0 ms | 180,3 ms |

La afirmación **sólo se cumple con el interruptor abierto**, y entonces el respaldo
cuesta ~65 ms. Los ~180 ms de la tabla son el p95 de la fase completa, que mezcla la
ventana anterior a la apertura —donde cada fallo espera el presupuesto íntegro— con la
posterior. Con el proveedor **lento** el interruptor no abre nunca, así que el camino
degradado (189 ms) es **más lento** que el camino frío con proveedor sano (159 ms).

El Anexo G predecía 110 ms para el camino degradado y 210 ms para el frío. Ambas cifras
deben rehacerse: el camino frío cuesta ~160 ms y el degradado depende del interruptor.

### HD-01.4 — C sostiene el umbral con acierto ≥ 96 % ❌ **refutada; hay que reescribirla**

Con el proveedor lento:

| Acierto | B: > 475 ms | B: p99 | C: > 475 ms | C: p99 | C: con respaldo |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 99 % | ✅ 0,29 % | 65 ms | — | — | — |
| 98 % | ✅ 0,73 % | 453 ms | — | — | — |
| 96 % | ❌ 1,28 % | 492 ms | ✅ 0,00 % | 186 ms | 3,7 % |
| 90 % | ❌ 3,06 % | 528 ms | ✅ 0,00 % | 188 ms | 9,2 % |
| 50 % | ❌ 16,75 % | 556 ms | ✅ 0,00 % | 190 ms | 49,2 % |

**En C la tasa de acierto no decide el percentil**: el peor caso es presupuesto + tarifa
(~190 ms) con cualquier acierto. Quien depende del acierto es **B**, y su mínimo está
entre el 96 % y el 98 %, es decir **alrededor del 97 %**.

Redacción propuesta:

> **HD-01.4** — Con el proveedor lento, el p99 de B cumple sólo con acierto ≥ 97 %. El
> p99 de C cumple con cualquier acierto; lo que depende del acierto es la proporción
> resuelta con respaldo.

**Cuidado con la segunda cláusula.** Cuando el proveedor no responde dentro del
presupuesto, la proporción con respaldo es ≈ 1 − acierto (3,7 % con 96 %, 9,2 % con
90 %, 49,2 % con 50 %). Exigir "respaldo ≤ 5 %" equivale a exigir "acierto ≥ 95 %": es
aritmética, no un resultado experimental. Lo que falta es el **umbral de respaldo que
actuaría considere aceptable**; ese número fija directamente el acierto necesario.

### HD-01.5 y HD-01.6 — el interruptor ⚠️ **se miden en B, no en C**

Con el proveedor sin respuesta:

| Política | Tráfico | B: > 475 ms | B: p99 | Abre en | C: > 475 ms |
| --- | --- | ---: | ---: | ---: | ---: |
| tasa | alto (200 sol/s) | ✅ 0,24 % | 65 ms | 7 s | 0,00 % |
| tasa | bajo (10 sol/s) | ✅ 0,77 % | 65 ms | 11 s | 0,00 % |
| conteo | alto | ✅ **0,07 %** | 65 ms | 5 s | 0,00 % |
| conteo | **bajo** | ❌ **1,19 %** | **716 ms** | 15 s | 0,00 % |

Es la interacción que HD-01.6 predecía: **con tráfico alto el conteo es la mejor
política; con tráfico bajo es la que rompe el ASR.** La política por tasa nunca
incumple y nunca gana: es la opción robusta.

**En C esto es invisible**: las cuatro celdas cumplen con holgura, porque ninguna
petición espera más que el presupuesto. En C el interruptor no protege la latencia,
protege el pool y al proveedor. HD-01.5 y HD-01.6 deben medirse sobre el tiempo hasta
la apertura, las llamadas desperdiciadas y las invocaciones en vuelo —y evaluarse en
el brazo B, si lo que se quiere es su efecto sobre la latencia.

### HD-01.7 — coalescencia ✅ **confirmada, con una celda nueva**

Con los pools de claves normales hubo **0 coalescencias** en las 8 corridas del bloque 3:
el sorteo uniforme sobre 10⁵–10¹² claves no produce fallos concurrentes sobre la misma
clave. La celda `b3_estampida_ttl2b` concentra el tráfico en **20 claves con TTL de 2 s**:

| Brazo | Coalescidas | En vuelo (pool = 40) | p99 |
| --- | ---: | ---: | ---: |
| C | 0 | ❌ **101** | 183 ms |
| C′ | **577** | ✅ **20** | 184 ms |

Sin coalescencia el pool se satura —101 invocaciones en vuelo sobre 40—; con
coalescencia queda en 20, una por clave. **La latencia apenas cambia** (183 contra
184 ms): la coalescencia protege el pool y al proveedor, no el percentil.

### HD-01.8 — recuperación ✅ **confirmada**

El interruptor cierra entre 5 y 14 s; la proporción con respaldo vuelve por debajo del
5 % entre 0 y 26 s; el pico de invocaciones al proveedor **no supera la línea base**
(por ejemplo 8,4 contra 10,3/s, y 16,7 contra 16,6/s en la celda de estampida). El
criterio pedía ≤ 60 s y ≤ 3×.

### EC-LAT-02 — horario pico ✅

Con el bloque 4 repetido, la latencia es **plana de 20 a 200 sol/s**: p95 de 65 ms y p99
entre 138 y 149 ms en los cuatro escalones, en B y en C. Multiplicar la carga por diez
no mueve el percentil.

### EC-LAT-07 — presupuesto por dependencia ✅ **con poco margen**

El p95 del adaptador es de **111–117 ms** contra los 120 ms de la restricción, y entre el
2,5 % y el 4,1 % de las llamadas lo superan. Se cumple, pero el margen es de pocos
milisegundos y depende de la distribución configurada en el doble, que es una hipótesis
sobre el proveedor real y no una medición contra él.

## 4. Hallazgos nuevos

1. **El interruptor rescata a la caché simple frente a un proveedor caído.** B cumple el
   ASR en `degradado`, `sin respuesta` y `caído`. Esto no estaba previsto en HD-01.2.
2. **El desacople es lo que protege frente al proveedor que falla a medias.** Con fallos
   intermitentes del 30 %, **el interruptor no llega a abrir en ningún brazo** —no se
   alcanzan ni diez fallos consecutivos ni el 50 % de la ventana— y aun así B incumple
   (1,10 %) y C cumple (0,00 %). Como el interruptor no interviene en ninguno de los dos,
   la diferencia es atribuible **sólo al desacople**. Es el argumento más fuerte del
   experimento, porque elimina la explicación alternativa.
3. **El estado `degradado` del diseño es, en la práctica, una caída.** Con 820 ± 120 ms
   todas las llamadas superan el timeout duro, así que se comporta casi igual que
   `sin respuesta`. El estado que de verdad separa los brazos es `lento`.
4. **La política del interruptor sólo importa en B**, y allí la elección tiene
   consecuencias medibles sobre el ASR.

## 5. Defectos del montaje encontrados y corregidos

Todos están documentados en `README.md`, sección *Desviaciones*, con su evidencia:

- El `origen` del perfil se guardaba en la caché: la edad del dato se reportaba como 0 y
  el camino caliente se etiquetaba como frío.
- La tasa de acierto derivaba durante la corrida por repoblado de la caché.
- El reloj de las fases iba atado a aritmética de `sleep`: una ventana entera llegó a
  caer fuera de la carga y la corrida se dio por válida.
- Las métricas de invocaciones contaban las llamadas que el interruptor corta sin
  llegar al proveedor: la recuperación aparecía como 200/s cuando llegaban 15.
- El escalón de 200 sol/s del bloque 4 corrió con acierto 0,86 en vez de 0,96, porque la
  dispersión de edad del pool caliente más la duración de la corrida superaban el TTL.
- `PoolTimeout` se contaba como falla del proveedor.
- `fig1`, la figura principal de HD-01.2, no se generaba por un fallo al partir el
  nombre de la corrida.

## 6. Lo que queda abierto

**Tres cosas que no se resuelven con corridas:**

1. **El umbral de respaldo aceptable.** El experimento mide la proporción; cuánto es
   admisible lo decide actuaría. Sin ese número, C gana por definición.
2. **La nomenclatura de tácticas** según el material del curso.
3. **El identificador de HA-01 en Jira**, que además `Estrategia-de-pruebas.md` asocia a
   HA-07.

**Una desviación declarada:** el Anexo B pide tres repeticiones y se corrió una, salvo
en la celda cercana al umbral (B con proveedor lento), que tiene tres: 1,28 %, 1,15 % y
1,24 %. La justificación es la varianza medida —p95 de 64,8 a 64,9 ms en seis corridas
independientes— y está escrita en el README.

**Dos amenazas a la validez que hay que declarar en el Anexo D:**

- El motor de tarifa es casi todo espera y no reproduce la competencia por CPU de un
  motor de reglas real.
- Un fallo intermitente de detección de carga que apareció una vez y no se pudo
  reproducir. Hoy está mitigado con reintento automático y diagnóstico.

## 7. Qué cambiar en el diseño y en la wiki

1. **§1.2.4 de la wiki**: separar el mérito del interruptor del mérito del desacople. El
   interruptor basta frente a un proveedor caído; el desacople hace falta frente al
   proveedor lento o intermitente.
2. **Modelo de fallas**: añadir el estado **intermitente** como sexto estado y declarar
   qué estado materializa el estímulo de `EC-LAT-09`. Hoy `lento` es el que corresponde
   a "no responde dentro de su presupuesto", y `degradado` es en la práctica una caída.
3. **HD-01.4, HD-01.5 y HD-01.6**: reescribirlas según §3.
4. **Anexo G**: rehacer el reparto interno del brazo C con los valores medidos.
5. **Anexo B**: unificar los cinco estados y declarar el umbral de respaldo como segunda
   medida de respuesta de `EC-LAT-09`.
6. **Aislamiento de recursos**: dimensionarlo también sobre las tareas de refresco, no
   sólo sobre las conexiones, y excluir `PoolTimeout` de las fallas del proveedor.

## 8. Dónde está la evidencia

| Qué | Dónde |
| --- | --- |
| Estado de las 52 corridas | `ESTADO_EXPERIMENTO.md` |
| Tabla completa por fase | `results/analysis/resultados_por_fase.csv` |
| Figuras del informe | `results/analysis/figuras/` |
| Evidencia cruda por corrida | `results/raw/<corrida>/` — métricas, configuración efectiva, verificaciones, series temporales segundo a segundo |
| Series completas de Prometheus | `results/prometheus/` (instantánea restaurable) |
| Desviaciones del montaje | `README.md`, sección *Desviaciones* |
