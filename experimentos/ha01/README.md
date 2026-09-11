# Experimento HA-01 — montaje

Protección del presupuesto de latencia de la cotización embebida frente a una
dependencia externa de Open Finance.

Documentos de referencia: `Diseno_Experimento_HA-01.md` (hipótesis, diseño
experimental, criterios de aceptación) e `Implementacion_Experimento_HA-01.md`
(guía técnica). Este README documenta **el montaje construido** y, sobre todo,
las **desviaciones deliberadas** respecto de esos documentos.

## Arranque rápido

```bash
cd experimentos/ha01
docker compose up -d --build            # levanta todo el montaje
./scripts/smoke.sh                      # prueba de humo: 4 brazos x 5 estados
```

Grafana en <http://localhost:3000> (anónimo, tablero *HA-01*), Prometheus en
<http://localhost:9090>.

Una corrida completa:

```bash
./scripts/run_block1.sh 3     # 45 corridas — HD-01.1, 01.2, 01.3
./scripts/run_block2.sh 3     # 24 corridas — HD-01.4
./scripts/run_block3.sh       #  8 corridas — HD-01.5 a 01.8
./scripts/run_block4.sh       #  4 corridas — tasa de llegada / EC-LAT-02
./scripts/collect_results.sh  # tablas del Anexo C en results/analysis/
```

> **9,8 horas** en total, medidas y no estimadas: 26 s de sobrecosto fijo por
> corrida (37 s cuando el pool vencido es grande), más 380 s de carga en los
> bloques 1–3 y 560 s en el 4 —360 y 540 s de fases más 20 s de margen para la
> variabilidad de arranque de k6—, más el drenaje. Bloque 1 ≈ 5,3 h, bloque 2 ≈
> 2,9 h, bloque 3 ≈ 1,0 h, bloque 4 ≈ 0,7 h. Es una ejecución desatendida: la
> máquina no puede estar haciendo otra cosa, o los percentiles dejan de ser
> comparables entre corridas.

## Campaña desatendida (recomendado)

```powershell
.\scripts\programar_campana.ps1 -Prueba   # comprueba que la tarea ve Docker, Python y la API
.\scripts\programar_campana.ps1          # registra y lanza la campaña completa
```

La campaña se registra en el **Programador de tareas de Windows** (`HA01-campana`)
para que no dependa de ninguna terminal, de VS Code ni de una sesión de Claude
Code: sigue corriendo aunque se cierre todo lo demás. Encadena los bloques en el
orden **3 → 1 → 2 → 4** y consolida la evidencia (CSV y figuras) al terminar cada
uno, así que si se corta a mitad de la noche lo ya medido queda analizado.

El bloque 3 va primero porque funciona como **compuerta**: ejercita los dos
extremos de tráfico, las dos políticas del interruptor y los dos niveles de
acierto. Si alguna de sus corridas falla, la campaña se detiene y espera a una
persona en vez de gastar nueve horas más sobre un montaje con problemas.

| Qué | Dónde |
| --- | --- |
| Estado en vivo | `results/campana_estado.txt` |
| Traza completa | `Get-Content results\campana.log -Wait -Tail 20` |
| Corridas a repetir | `results/corridas_fallidas.txt` |
| Detenerla | `Stop-ScheduledTask -TaskName HA01-campana` |
| Borrar las tareas | `.\scripts\programar_campana.ps1 -Quitar` |

Antes de lanzarla: portátil **enchufado**, hibernación y suspensión con corriente
en *nunca* (`powercfg /change hibernate-timeout-ac 0`) y el equipo sin otro uso
durante ~10 h.

## Umbral

**225 ms (p95) y 475 ms (p99) medidos en el servicio.** No 250/500. El montaje
no incluye `:ApiGateway` y el Anexo G reserva 25 ms para el borde. Si aparece
un 250 en un `threshold`, se está midiendo contra el umbral equivocado.

## Los cuatro brazos

Viven en el mismo binario y se seleccionan con `QUOTE_STRATEGY`. Es la única
variable que cambia entre corridas del bloque 1.

| Brazo | `QUOTE_STRATEGY` | En fallo de caché |
| --- | --- | --- |
| A | `direct` | invoca y espera, sin caché |
| B | `cache_blocking` | invoca y **espera** antes de responder |
| C | `cache_opportunistic` | responde con respaldo; el refresco sigue en fondo |
| C-prima | `cache_singleflight` | igual que C, más coalescencia por clave |

## Los cinco estados del proveedor

`./infra/toxiproxy/states.sh <sano|lento|degradado|sin_respuesta|caido>`, en
caliente y sin reiniciar nada.

---

## Desviaciones respecto de los documentos publicados

Las siguientes decisiones **se apartan** de lo escrito en el documento de
diseño o en la guía de implementación. Cada una corrige un defecto que habría
invalidado la medición; todas deben quedar registradas en el informe.

### 1. El origen del perfil no se almacena en la caché

La guía guardaba `origen` dentro del blob de Redis. Un perfil escrito por el
adaptador y leído después desde la caché seguía diciendo `open_finance`, con
dos consecuencias: la **edad del dato se reportaba como 0** para datos viejos,
y el camino caliente se etiquetaba como camino frío en
`ha01_quote_latency_seconds`, que es justo la métrica de **HD-01.3**. Ahora el
origen lo decide la estrategia y viaja en un objeto `Resolucion` aparte.

### 2. Tasa de acierto estacionaria: tres pools de claves

La precarga original dejaba ausente el `1 - acierto` del universo, pero cada
fallo **repuebla** la caché: con el proveedor sano la tasa de acierto sube
durante la corrida. Como es la variable independiente del bloque 2, no puede
derivar mientras se mide. El montaje usa tres pools disjuntos que k6 sortea
(`load/k6/claves.js`) y que `warm_cache.py` precarga:

| Pool | Prefijo | Estado en Redis | Resuelve a |
| --- | --- | --- | --- |
| Caliente | `cli_h*` | fresco (edad ≤ TTL) | `cache` |
| Vencido | `cli_s*` | presente, edad > TTL | `fallback` si el proveedor falla |
| Frío | `cli_c*` | **ausente** | `default` si el proveedor falla |

Los pools de fallo son mucho mayores que el número de fallos de una corrida
(a 100 sol/s y 4 % de fallo son ~1400 claves sobre 100 000), así que la
probabilidad de volver a sortear una clave ya repoblada queda por debajo del
1 %, dentro de la tolerancia de ±2 puntos de `verify_hitrate.sh`.

El pool **vencido** existe porque los dos caminos de degradación no son el
mismo: sin valor previo el brazo C tarifica con el perfil por defecto y nunca
ejercitaría el *último valor conocido*, que es la mitad de la táctica bajo
prueba. `MISS_STALE_FRACTION` reparte los fallos entre ambos.

### 3. "Peticiones sacrificadas" se separa en dos métricas

El documento usaba un solo contador para dos cosas distintas. En A y B una
llamada fallida equivale a una petición de usuario con latencia inflada; en C
**el usuario ya recibió respuesta** y lo que falla es un refresco de fondo.
Con un solo número, el criterio "< 1 % de la ventana" no significa lo mismo en
cada brazo.

- `ha01_llamadas_fallidas_proveedor_total` — salud del adaptador.
- `ha01_cotizaciones_degradadas_total` — **impacto real al socio**; sobre esta
  se evalúa el criterio de aceptación de HD-01.5.

Consecuencia para el diseño: **HD-01.5 y HD-01.6 deben reescribirse** en esos
términos. Además, el conteo de sacrificadas está acotado por el propio umbral
del interruptor, así que a tráfico bajo nunca superaría el 1 % con ninguna
política; la métrica que discrimina entre políticas es el **tiempo hasta la
apertura**, que `analizar.py` reporta como `s_hasta_abrir`.

### 4. El interruptor limita las sondas en semiabierto

`permite()` dejaba pasar **todas** las peticiones mientras el estado fuera
semiabierto. Con el proveedor colgado a 100 sol/s eso son cientos de sondas
simultáneas contra un proveedor que apenas se recupera: exactamente la
estampida que HD-01.8 dice que no debe ocurrir. Ahora `BREAKER_HALF_OPEN_PROBES`
—que estaba en el `.env` sin usarse— acota las sondas concurrentes.

Además, la ventana deslizante **se vacía al cerrar**: si conservara los fallos
previos, el primer fallo posterior reabriría de inmediato y el interruptor
oscilaría durante toda la fase de recuperación, falseando el tiempo hasta
cerrar de HD-01.8.

### 5. Referencias fuertes a las tareas de refresco

`asyncio` sólo mantiene referencias débiles a las tareas. Con el `create_task`
en una variable local que muere al vencer el presupuesto, el recolector puede
llevarse una tarea a medio vuelo: la caché no se repoblaría y el brazo C
estaría midiendo otra cosa sin que nada lo delate. `Contexto` mantiene el
conjunto de tareas vivas, consume sus excepciones y lo expone como
`ha01_refrescos_fondo_activos` para poder detectar la fuga.

### 6. `caido` deshabilita el proxy en vez de usar `reset_peer`

El modelo de fallas describe `caido` como **conexión rechazada**. La toxina
`reset_peer` en `downstream` establece la conexión, envía la petición y
resetea recién cuando el upstream responde (~60 ms), así que no contrastaba
con `sin_respuesta` como el diseño supone. Deshabilitar el proxy sí produce un
*connection refused* real.

También se corrigió `limpiar()`: el `json.load(sys.stdin)` se ejecutaba dos
veces sobre el mismo stdin, la segunda fallaba con la entrada agotada, el
`|| true` se tragaba el error y **las toxinas se acumulaban entre estados**.

### 7. El doble es determinista por cliente, no por secuencia

Un `random.Random` global consumido por corrutinas concurrentes produce
secuencias que dependen del entrelazado: dos repeticiones con la misma semilla
dejaban de ser comparables. La latencia se deriva ahora por hash de
`(PROVIDER_SEED, customer_id)`, lo que además la hace estable por cliente.

**Sobre los tres percentiles.** La log-normal queda determinada por p50 y p95;
el p99 **no se controla**. Con 60/110 ms el p99 realizado es ~141 ms, no los
180 configurados, que sólo actúan como cota de la cola. `verify_provider.sh`
imprime el contraste y el recurso `/perfil-latencia` lo expone.

### 8. Un solo worker de Uvicorn

El interruptor y el registro Prometheus viven en proceso. Con
`UVICORN_WORKERS=2` habría dos interruptores independientes y el scrape caería
en uno u otro, dejando `ha01_breaker_*`, `ha01_adapter_inflight` y la tasa de
acierto sin sentido.

### 9. Correcciones menores

- `main.py` invocaba `_edad_segura`, que no existía, y no exponía `/metrics`
  pese a que Prometheus lo raspa. Se añadió además `/info` con la
  configuración efectiva de la corrida, que el protocolo archiva: sin ella un
  resultado no es auditable seis semanas después.
- `k6 run --duration 60s` **se ignora** cuando el script declara `scenarios`;
  la duración se pasa por `-e DURATION`.
- `-o experimental-prometheus-rw` estaba como flag de `docker compose run` y
  no de `k6 run`. La imagen de k6 queda fijada en 0.55.0 porque en k6 ≥ 1.0
  ese *output* pasa a llamarse `prometheus-rw`.
- Etiquetas del interruptor: `Estado(str, Enum)` produce `"Estado.CERRADO"` al
  pasar por `str()`. Se usa `.value`.
- `maxmemory` de Redis a 512 MB: con tres pools el dataset ronda los 80 MB y
  una evicción por LRU cambiaría la tasa de acierto en silencio.
  `verify_run.sh` comprueba `evicted_keys == 0`.
- El adaptador no abre el interruptor ante un 4xx: un 429 por cuota es un
  error de negocio, y castigar al proveedor por nuestra propia tasa de llamada
  confundiría dos modos de falla distintos.

### 10. Un solo proceso de k6 por corrida, con rodaje no contabilizado

El protocolo original invocaba k6 dos veces: una de calentamiento y otra de
medición. Eso calienta la API pero **no a k6**, cuyo arranque —asignar cientos
de VUs, cada una con su runtime de JS— consume CPU en la misma caja que el
sistema bajo prueba.

Medido a 200 sol/s: k6 escaló a **913 VUs**, el *event loop* de la API estuvo
al **99,8 %** (un núcleo entero, el techo de un worker) durante 12 s, con
**p95 = 5,08 s** y **516 iteraciones descartadas**. A partir del segundo 12 se
estabilizó en 12 VUs, 200/s exactos y mediana de 61 ms. El transitorio caía
**dentro de la fase sana** de todas las corridas.

Ahora hay un solo proceso de k6 cuyos primeros `ESTABILIZACION_S` segundos no
se contabilizan: las marcas de fase se toman después. Tras el cambio, la misma
corrida da **40 000 iteraciones, 0 descartadas** y p95 de 64,8 ms en fase sana.

`maxVUs` bajó de `RATE*10` a `RATE*4` para que k6 descarte iteraciones en vez
de entrar en la espiral, y **el descarte ahora se comprueba**
(`verify_run.sh`): es la razón entera por la que el diseño elige el ejecutor de
tasa de llegada, y hasta ahora nadie lo miraba.

### 11. Límites de recursos en los cuatro servicios que no los tenían

El Anexo A declara los límites de CPU y memoria como **variable controlada**,
pero `toxiproxy`, `prometheus`, `grafana` y `k6` corrían sin ninguno
(verificado con `docker inspect`: `NanoCpus=0`). El grave era k6, por lo
descrito arriba. Ahora los ocho servicios los declaran. Suman **9,5 CPU** (API 2, k6 2,
doble 1,5, Redis 1, Toxiproxy 1, Prometheus 1, Postgres 0,5, Grafana 0,5)
frente a los 8 de la VM: son topes, no reservas, y el consumo real a
200 sol/s queda muy por debajo, así que la sobresuscripción no se materializa.

### 12. Las marcas de fase se toman del reloj de Prometheus

`analizar.py` corta las fases consultando a Prometheus, que sella sus muestras
con el reloj de la VM. Tomarlas del reloj de Windows funciona mientras ambos
coincidan —hoy el desfase es 0 s— pero el reloj de WSL2 deriva cuando el equipo
suspende, y una corrida desatendida de nueve horas es justo ese escenario.

### 13. Bloque 3 ampliado y bloque 4 nuevo

**HD-01.7 no era observable como estaba planteado.** Con acierto 96 % a
200 sol/s hay 8 fallos/s; a 700 ms de timeout duro eso son 5,6 invocaciones
concurrentes sobre un pool de 40 —el 14 %— y el interruptor abre a los ~6 s,
con lo que la ventana en que el pool podría llenarse dura esos 6 s. Medido:
`inflight_max = 8`. Para saturar 40 conexiones hacen falta 57 invocaciones por
segundo, o sea un 28,6 % de fallos. El bloque 3 corre ahora el contraste C
contra C′ **también con acierto 50 %** (100 fallos/s → 70 concurrentes). Que a
96 % el pool no se estrese es un resultado en sí mismo: el interruptor actúa
antes que el aislamiento de recursos.

**La tasa de llegada estaba declarada como variable independiente con niveles
20/50/100/200 pero ningún bloque la variaba** —el 1 y el 2 la fijan en 100, el
3 usa 200 y 10— así que dos de los cinco niveles no se ejecutaban nunca. El
bloque 4 los recorre con `cotizacion.js` y da la curva de latencia contra
carga, que es lo que sostiene `EC-LAT-02` (horario pico, "alta concurrencia").

Los tramos a analizar viven ahora en `fases.json`, común a los cuatro bloques:
tres fases en el 1–3, un tramo por escalón en el 4, un solo camino de análisis.

### 14. Los pools de fallo se dimensionan desde la deriva admisible

Los tres pools de la desviación 2 resuelven la deriva de la tasa de acierto a
96 %, pero **no a 50 %**, y eso solo se vio al correr esa celda. La deriva
aparece en las fases sanas: un refresco con éxito convierte una clave vencida
en fresca, y la próxima vez que salga sorteada será un acierto en vez de un
fallo. En puntos porcentuales:

```
deriva = (1 - acierto) × fracción_vencida × (repobladas / POOL_STALE)
```

Con 100 000 claves, acierto 50 % y 200 sol/s durante los 240 s sanos del
protocolo real, eso da **3 puntos**: el doble de la tolerancia de
`verify_hitrate.sh`. Con las fases cortas de un piloto daba 1,5 y pasaba, que
es exactamente cómo se coló.

Dos correcciones:

- **El pool frío deja de ser finito.** Los ids se sortean sobre 10¹², así que
  una clave fría repoblada no vuelve a salir nunca y su aporte a la deriva es
  cero. El pool vencido no puede hacer lo mismo: necesita un valor previo
  realmente precargado, luego es finito por fuerza.
- **El pool vencido se dimensiona desde la aritmética de cada corrida**
  (`pool_vencido()` en `_comun.sh`), con la deriva admisible como parámetro.
  A 96 % se queda en 100 000; a 50 % y 200 sol/s sube a 600 000 (~168 MB, por
  lo que `maxmemory` de Redis pasa a 1 GB).

El tamaño se calcula **una sola vez en bash** y se pasa tanto a `warm_cache.py`
como a k6: si los dos números no coincidieran, k6 sortearía sobre un rango
distinto del precargado y la tasa de acierto observada no sería la configurada.
Es el fallo más silencioso que admite este montaje.

Verificado con las fases reales, acierto 50 % a 200 sol/s: deriva predicha
+0,50 puntos, **observada +0,38**. Y con el pool ya bien dimensionado, HD-01.7
por fin es observable — `inflight_max` llega a **80 sobre un pool de 40**, o
sea 40 conexiones activas y 40 encoladas.

### 15. La verificación de la línea base se mide pareada

`verify_baseline.sh` comparaba `mediana(via_proxy)` contra `mediana(directo)`
sobre dos bloques de 120 peticiones. **Ese estimador no resolvía la cantidad que
decía medir.** Medido sobre 400 pares en este montaje:

| n peticiones | estimador | IC 95 % | ancho |
| ---: | --- | --- | ---: |
| 60 | no pareado | [−5,94, +9,27] ms | 15,21 |
| 120 | no pareado | [−4,00, +7,05] ms | 11,05 |
| 480 | no pareado | [−1,40, +4,17] ms | 5,58 |
| **60** | **pareado** | **[+0,39, +1,60] ms** | **1,21** |

El intervalo del estimador no pareado es más ancho que el propio umbral de 3 ms
con cualquier tamaño de muestra asumible. Se notaba en los resultados: cuatro
ejecuciones dieron +0,5, −1,3, −2,0 y −1,3 ms, y Toxiproxy **no puede acelerar
nada**. El 24 % de los pares sale negativo individualmente; ésa es la magnitud
del ruido.

La causa es que el montaje permite un diseño pareado y no se estaba usando: el
doble deriva su latencia por hash del `customer_id`, así que la latencia de
aplicación es idéntica para el mismo id en ambas series y al restar se cancela
—y es la fuente de varianza dominante. Ahora se mide `mediana(via_proxy_i −
directo_i)` sobre 30 pares, **alternando el orden petición a petición** para que
una deriva de carga entre bloques no contamine la diferencia, y se reporta el
intervalo de confianza por bootstrap.

Tres ejecuciones consecutivas del script corregido: +0,85, +1,04 y +1,11 ms.
Dispersión de 0,26 ms contra los 2,5 ms de antes, y todas del signo físicamente
posible. De paso el chequeo baja de 21,4 s a 8,4 s, que sobre 81 corridas son
18 minutos.

**Menos muestras, más confianza.** Es el caso en que el tamaño de muestra no era
el problema.

### 16. El reloj de las fases va atado a la carga real, no a `sleep`

**Es el defecto más peligroso que apareció en todo el montaje**, y sólo se vio
al ejercitar los caminos que ningún piloto había tocado.

Las marcas de fase se tomaban con aritmética de `sleep` desde el momento de
lanzar `docker compose run`. Pero entre lanzar el contenedor y que k6 empiece a
emitir pasa un tiempo **variable**, y en una traza medida esa ventana entera
quedó **fuera de la carga**: las tres fases sin una sola petición.

Lo grave no es el desfase sino que **la corrida se dio por válida**. El volcado
final decía 15 001 cotizaciones y las nueve verificaciones pasaban, porque
todas miraban **contadores acumulados**, que no dicen nada sobre si la ventana
está bien puesta. En una campaña desatendida de nueve horas eso son 81 corridas
con tablas llenas de ceros y ningún aviso.

Tres defensas, en capas:

1. **`esperar_carga`** — la ventana no abre hasta que el contador de la API
   crece en dos lecturas seguidas. Dos y no una: un solo incremento podría ser
   el rastro de un k6 anterior apagándose.
2. **`carga_viva`** — justo antes de abrir la ventana se vuelve a comprobar que
   la carga sigue emitiendo. Si k6 terminó durante el rodaje, se aborta ahí en
   vez de descubrirlo seis minutos después. k6 corre además con un margen
   (`MARGEN_CARGA_S`, 20 s) por encima de lo que duran las fases.
3. **`verify_run.sh` comprueba que cada fase contenga tráfico**, consultando a
   Prometheus con los cortes de `fases.json`. Es la comprobación que faltaba y
   la única que caza el caso ya consumado.

Y un cambio de política: **una corrida que no pasa las verificaciones ahora
falla**. Antes se imprimía un aviso y se seguía, con lo que una corrida
inválida acababa igualmente en el CSV. Ahora `corrida_segura` la registra y
`resumen_bloque` la lista al final como pendiente de repetir.

> **Nota de trazabilidad.** Este cambio de política se describió en un commit
> anterior pero no quedó aplicado hasta el 10/09 a las 21:15: el reemplazo de
> texto no encontró la cadena y falló sin avisar. No enmascaró ningún resultado
> —las 14 corridas ejecutadas mientras tanto pasaron todas sus verificaciones,
> como consta en su `sanidad.txt`—, pero se deja constancia.

### 17. Un fallo no se lleva por delante el resto del bloque

Los scripts de bloque llevan `set -e`: un fallo en la corrida 40 de 45 perdía
las cinco restantes, y a las cuatro horas y media de una ejecución desatendida
nadie está mirando. Ahora cada corrida se lanza con `corrida_segura`, que la
ejecuta en un **proceso aparte** y registra el fallo sin tumbar el bloque; si
fallan tres seguidas se aborta, porque eso ya no es una corrida mala sino el
montaje caído.

Tiene que ser un proceso y no un subshell: bash desarma `set -e` para todo lo
que cuelga de la condición de un `if` o del lado izquierdo de un `||`, y ese
desarme **se hereda** en los subshells. Comprobado: ni `( f )`, ni
`( set -e; f )`, ni `rc=0; ( set -e; f ) || rc=$?` detienen la función en el
punto que falla — las tres siguen ejecutando los pasos posteriores, que es peor
que abortar, porque la corrida continuaría con la caché mal precargada o el
proveedor en el estado que no es.

Además, una corrida que falla se **reintenta una vez**. El intento fallido se
conserva en `<corrida>__intento1_fallido` y queda anotado en
`corridas_fallidas.txt`. Reintentar no sesga el resultado: las verificaciones
juzgan si el instrumento midió bien —tráfico en cada fase, acierto, descartes,
fugas—, nunca si se cumple el ASR.

### 18. Plan reducido en lugar de 3 repeticiones de los bloques 1 y 2

El Anexo A pide 3 repeticiones contrabalanceadas de los bloques 1 y 2 (~8,8 h).
Se ejecuta en su lugar `run_plan_reducido.sh` (~3,4 h), con esta justificación:

- **La variación entre corridas medida es mínima.** En el bloque 3, el p95 en
  fase sana fue de 64,8–64,9 ms en seis corridas independientes y el p99 de
  133–147 ms, a más de 3 veces del umbral. Una repetición no puede mover un
  resultado que está al triple de distancia; donde sí hace falta repetir es en
  las celdas cercanas al umbral.
- **Se replica sólo la celda cercana al umbral:** B con proveedor lento
  (1,28 % de cotizaciones sobre 475 ms, contra el 1 % permitido).
- **El bloque 2 corre en `lento`, no en `degradado`.** En `degradado` el
  interruptor abre en segundos y rescata a B, así que la curva no discriminaría
  entre brazos. Se añade el nivel del **98 %**, porque el cruce de B parece
  estar entre 96 y 99 %.
- Con una sola repetición el contrabalanceo pierde sentido. El riesgo de un
  efecto de orden es bajo porque cada corrida reinicia la API, vacía la caché y
  restablece el proveedor.

### 19. Celda de estampida para HD-01.7

En el bloque 3 hubo **0 coalescencias** en las 8 corridas, también con C′. Los
pools de claves de la desviación 2 hacen que dos fallos simultáneos sobre la
*misma* clave casi no ocurran, así que C′ no tenía nada que coalescer. La celda
`b3_estampida_ttl2` concentra todo el tráfico en **20 claves con TTL de 2 s**:
cada clave vence cada 2 s y recibe ~10 peticiones por segundo. Con el proveedor
`sin_respuesta`, C lanza un refresco por petición y C′ uno por clave.

Verificado en una prueba corta: C′ coalesció 606 peticiones en la fase
degradada, con 19 invocaciones en vuelo como máximo (una por clave) y 0,65
invocaciones por fallo de caché, frente a la 1,0 que da siempre C. En esta
celda la tasa de acierto **no es la variable** y no se verifica
(`VERIFICAR_ACIERTO=0`).

### 20. Detector de interferencia

Una sonda dentro de la API duerme 100 ms en bucle y registra cuánto se retrasa
el bucle de eventos (`ha01_event_loop_lag_seconds`). `verify_run.sh` marca la
corrida como **sospechosa**, sin invalidarla, si el retraso p99 supera 50 ms o
hay algún parón de más de 250 ms. La sonda no distingue la carga propia del
worker de la competencia por CPU con otros procesos del equipo, pero sí dice si
la cola de latencia de una corrida está contaminada. Las corridas anteriores al
10/09 21:10 no tienen esta métrica. Su costo es despreciable: 10 despertares
por segundo frente a 100–200 cotizaciones por segundo.

### 21. Evidencia versionada y autocontenida

Al cerrar cada corrida, su carpeta recibe sus resultados por fase
(`fases_resultado.json`) y sus series temporales segundo a segundo
(`series.csv`), de modo que el análisis se puede rehacer sin Prometheus. Se
regenera `ESTADO_EXPERIMENTO.md` y todo se sube al repositorio. Al cerrar la
campaña se versiona además una instantánea comprimida de toda la base de
Prometheus (`results/prometheus/`).

---

## Evidencia para el informe

### Por corrida — `results/raw/<brazo>_<run_id>/`

| Archivo | Qué contiene |
| --- | --- |
| `api_metrics.txt` | volcado final de todas las métricas de `:MsCotización` y `:AdaptadorOF` |
| `provider_metrics.txt` | métricas del doble; contrasta con las del adaptador |
| `api_info.json` | **configuración efectiva**: brazo, presupuesto, timeout, política y estado del interruptor, tamaño del pool, TTL, claves en Redis, si las reglas vinieron de la BD |
| `env.txt` | todas las variables de la corrida |
| `fases.json` | los cortes temporales de cada fase o escalón |
| `sanidad.txt` | resultado de las nueve verificaciones; si falla, la corrida no es válida |
| `k6_summary.json` | medida **de cliente**, incluido `dropped_iterations` |
| `k6_stdout.txt` | traza completa de k6 |
| `stats.csv` | CPU y memoria de cada contenedor al terminar |
| `toxiproxy.json` | toxinas activas, para confirmar el estado inyectado |

`api_info.json` y `env.txt` son lo que hace **auditable** un resultado seis
semanas después: sin ellos, un número en una tabla no se puede reproducir.

### Consolidado — `results/analysis/`

| Archivo | Qué contiene |
| --- | --- |
| `resultados_por_fase.csv` | una fila por fase de cada corrida: p50/p95/p99, error, % con respaldo, edad p50/p95, acierto observado, estado máximo del interruptor, invocaciones en vuelo, refrescos, coalescidas, p95 **por camino**; más una fila `transiciones` con los tiempos hasta abrir y hasta cerrar |
| `figuras/*.png` | las figuras del informe, 200 ppp |
| `enlaces_grafana.md` | un enlace por corrida al tablero, **ya acotado a su ventana** |

### Las figuras

`./scripts/collect_results.sh` las genera junto con el CSV. Cada una sale sólo
si hay datos de su bloque, así que se puede ejecutar con los bloques a medio
correr.

| Figura | Qué sostiene |
| --- | --- |
| `fig1_brazo_x_estado.png` | Bloque 1: p95 y p99 por brazo × estado, con las líneas de 225 y 475 ms — **HD-01.1, HD-01.2** |
| `fig2_camino.png` | p95 por camino de resolución (caché / open_finance / fallback / default) — **HD-01.3** |
| `fig3_acierto.png` | p95 y p99 contra tasa de acierto; el cruce con el umbral da el mínimo — **HD-01.4** |
| `fig4_serie_<corrida>.png` | serie temporal de una corrida: latencia, estado del interruptor y % con respaldo en tres paneles con eje de tiempo compartido — **HD-01.8** |
| `fig5_carga.png` | latencia contra tasa de llegada — **EC-LAT-02** |
| `fig6_frescura.png` | % con respaldo y edad del dato por fase y brazo — **el trade-off de §2.8** |
| `fig7_pool.png` | invocaciones en vuelo contra el tamaño del pool — **HD-01.7** |

La paleta está validada (banda de luminosidad, piso de croma, separación para
daltonismo y contraste). Dos de las cuatro ranuras quedan por debajo de 3:1
contra la superficie, así que **toda barra lleva su valor escrito** y el CSV
sirve de vista de tabla equivalente.

`fig4` usa tres paneles apilados y no dos escalas verticales: superponer
latencia y estado del interruptor sobre ejes distintos es la forma más común de
mentir con un gráfico.

Las figuras se generan en un contenedor aparte (`analisis/Dockerfile`) para no
meter matplotlib en la imagen que se mide, y para que la máquina del analista no
necesite instalar nada.

### Grafana en vivo

<http://localhost:3000>, tablero *HA-01*, diez paneles. Prometheus conserva
**30 días**, así que los enlaces de `enlaces_grafana.md` siguen sirviendo
después de terminar las corridas.

---

## Amenaza a la validez que el montaje no resuelve

`RATING_COST_MS=60` con `RATING_CPU_ITERS=1200` es, en la práctica, casi todo
espera: el trabajo de CPU real es del orden de décimas de milisegundo. No
sesga la comparación entre brazos —es idéntico en todos— pero el montaje **no
reproduce la competencia por CPU** de un motor de reglas real. Debe declararse
en el Anexo D junto con las amenazas ya listadas.

## Trazabilidad pendiente

El documento de diseño asocia el experimento a **HA-01**, pero
`Estrategia-de-pruebas.md` asocia `EC-LAT-09` a **HA-07**. Hay que reconciliar
el identificador en Jira antes de publicar. El Anexo B menciona "los cuatro
estados" cuando el modelo define cinco, y el Anexo F lista "HD-01.1 a HD-01.7"
habiendo ocho sub-hipótesis.

## Nota de entorno (Windows)

- **`C:\Users\<usuario>\.wslconfig`** acota la VM de WSL2 en la que corre Docker:

  ```ini
  [wsl2]
  memory=6GB
  swap=0

  [experimental]
  autoMemoryReclaim=gradual
  ```

  Sin techo, WSL puede crecer hasta el 50 % de la RAM y, junto con Windows,
  no cabe en un equipo de 16 GB: paginación durante la campaña. `swap=0` es
  deliberado en un experimento de latencia: paginar metería pausas en silencio
  en los percentiles, mientras que quedarse sin memoria hace fallar la corrida
  de forma visible. Verificado: la VM pasa de 8,24 a 6,22 GB, conserva los 8
  CPU, y el montaje en marcha usa ~0,9 GB. Para deshacerlo: borrar el archivo,
  `wsl --shutdown` y reabrir Docker Desktop.

- Docker Desktop debe estar corriendo antes de `docker compose up`.
- Los scripts son bash: ejecutarlos desde Git Bash, no desde PowerShell.
- El proyecto vive en OneDrive con espacios en la ruta. Conviene **pausar la
  sincronización** durante las corridas para que OneDrive no toque `results/`
  mientras k6 escribe.
