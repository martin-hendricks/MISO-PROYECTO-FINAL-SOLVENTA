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

> El bloque 1 tarda del orden de **6 horas** y los cuatro juntos **10–12**. Es
> una ejecución desatendida: la máquina no puede estar haciendo otra cosa, o
> los percentiles dejan de ser comparables entre corridas.

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
descrito arriba. Ahora los siete servicios los declaran y suman 8 CPU, que es
justo lo que la VM ofrece.

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

- Docker Desktop debe estar corriendo antes de `docker compose up`.
- Los scripts son bash: ejecutarlos desde Git Bash, no desde PowerShell.
- El proyecto vive en OneDrive con espacios en la ruta. Conviene **pausar la
  sincronización** durante las corridas para que OneDrive no toque `results/`
  mientras k6 escribe.
