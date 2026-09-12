# Auditoría de la ejecución del experimento HA-01

_Auditoría independiente de la ejecución contra el diseño publicado._

| | |
| --- | --- |
| **Objeto auditado** | `experimentos/ha01/` — 52 corridas, cerradas el 11/09/2026 20:38 |
| **Contra qué se audita** | `wiki/files/Diseno_Experimento_HA-01.md` (v1.0) y `wiki/Hoja-de-trabajo-semana-5.md` (arquitectura vigente) |
| **Fecha de la auditoría** | 12/09/2026 |
| **Método** | Verificación de cada cifra citada contra `results/analysis/resultados_por_fase.csv` y `results/raw/<corrida>/`; lectura del código de los cuatro brazos, del adaptador, del interruptor, del doble y de los scripts de protocolo; recálculo independiente de los percentiles del adaptador desde los *buckets* de Prometheus |

---

## 1. Veredicto de la auditoría

**El experimento es válido y sus conclusiones principales se sostienen.** La ejecución
es de una calidad metodológica notablemente alta: el equipo encontró y documentó 21
desviaciones respecto del diseño, varias de las cuales habrían invalidado la medición
si hubieran pasado inadvertidas —en particular el reloj de fases atado a `sleep`
(desviación 16) y la deriva de la tasa de acierto (desviaciones 2 y 14)—. La
autocrítica del `EVALUACION_AVANCE_HA01.md` es en general honesta y corrige
observaciones previas propias marcándolas como incorrectas.

**Pero la auditoría encontró tres defectos que no están declarados y que sí afectan
conclusiones publicadas**, uno de ellos en una afirmación de cumplimiento de una
restricción arquitectónica (`EC-LAT-07`). Ninguno derriba la hipótesis central, pero
los tres deben corregirse antes de que el informe se publique.

| # | Hallazgo | Severidad | Afecta a |
| --- | --- | :---: | --- |
| H-1 | `EC-LAT-07` se declara cumplido con cifras calculadas sobre contadores acumulados de toda la corrida, dominados por las fases sanas. En la fase degradada el p95 del adaptador es **472 ms, no 111–117 ms** | 🔴 **Alta** | Cumplimiento de `EC-LAT-07` |
| H-2 | En el estado `intermitente` el fallo es **determinista por cliente**, no aleatorio por petición: el mismo cliente falla siempre. No es un proveedor intermitente sino un subconjunto fijo de clientes rotos | 🟠 **Media** | Hallazgo nuevo nº 2, el "argumento más fuerte del experimento" |
| H-3 | El brazo A "cumple" el ASR con proveedor `caído` resolviendo el **98,9 % de las cotizaciones con el perfil por defecto**. Es cumplimiento de latencia con cero señal de Open Finance; la tabla de HD-01.2 lo presenta como ✅ sin esa salvedad | 🟠 **Media** | Tabla de HD-01.2, comparabilidad entre brazos |
| H-4 | `toxiproxy.json` se captura **después** de restaurar el estado sano: las 52 corridas guardan `"toxics":[]`. La evidencia del estado inyectado no existe | 🟡 **Baja** | Auditabilidad, no los resultados |
| H-5 | El p95 del adaptador no lo calcula `analizar.py`: las cifras de `EC-LAT-07` no son reproducibles desde el pipeline | 🟡 **Baja** | Reproducibilidad |

---

## 2. Lo que la ejecución hizo bien

Conviene decirlo con precisión, porque es la parte mayoritaria del trabajo.

**El control experimental es sólido.** Los cuatro brazos viven en el mismo binario y se
seleccionan por `QUOTE_STRATEGY` (`api/strategies.py`), de modo que la estrategia de
resolución del perfil es efectivamente la única variable que cambia. El contrato de
respuesta es idéntico por construcción. El motor de tarifa tiene costo fijo. El
interruptor arranca cerrado en cada corrida porque el protocolo reinicia la API y vacía
Redis (`_corrida.sh`, paso 1).

**La implementación del brazo C es correcta y hace lo que la hipótesis dice.** El
`asyncio.shield` dentro del `wait_for` (`strategies.py:127`) es exactamente lo que
impide que el brazo C degenere en un brazo B con timeout más corto — sin él, `wait_for`
cancelaría la tarea al vencer el presupuesto y no habría actualización oportunista. El
comentario del código lo explica. Verificado también que el adaptador **no** conoce
`DEPENDENCY_BUDGET_MS` (`adapter.py`, docstring), que es la separación de los dos
relojes que la hipótesis pone a prueba.

**Las verificaciones de sanidad son reales y se ejecutan.** Cada corrida archiva
`sanidad.txt` con las nueve comprobaciones, incluida la que faltaba y es la que caza el
defecto del reloj de fases: tráfico presente en cada fase. Revisado el conjunto: las 52
corridas pasan.

**Tres decisiones de instrumentación merecen crédito explícito:**

- Separar `llamadas_fallidas_proveedor` de `cotizaciones_degradadas` (desviación 3). Sin
  esa separación, el criterio "< 1 % de la ventana" de HD-01.5 significa cosas distintas
  en A/B que en C, y la comparación no sería legítima.
- Excluir `PoolTimeout` de las fallas del proveedor (`adapter.py:76-83`). Contar
  saturación propia como falla del tercero abriría el interruptor con el proveedor sano.
- No abrir el interruptor ante un 4xx (`adapter.py:64-70`). Un 429 por cuota es un error
  de negocio, no de disponibilidad.

**El estimador pareado de la línea base (desviación 15)** es un acierto estadístico
real: el intervalo de confianza pasa de ±7 ms a ±1 ms con **menos** muestras, porque el
diseño pareado cancela la fuente de varianza dominante. La observación de que cuatro
ejecuciones daban signo negativo —y que Toxiproxy no puede acelerar nada— es la clase de
verificación de cordura que la mayoría de los montajes no hace.

---

## 3. Hallazgos

### H-1 🔴 `EC-LAT-07` no está demostrado; en la fase degradada se incumple

**Qué afirma el `EVALUACION_AVANCE_HA01.md` (§3, "EC-LAT-07"):**

> El p95 del adaptador es de **111–117 ms** contra los 120 ms de la restricción, y entre
> el 2,5 % y el 4,1 % de las llamadas lo superan. Se cumple, pero el margen es de pocos
> milisegundos.

Ese mismo documento usa esta cifra para marcar como **incorrecta** una observación
previa propia (§2, fila §4.6: *"El camino frío no cabe en EC-LAT-07 — ❌ incorrecta"*).

**Qué muestra la evidencia.** Recalculé el p95 del adaptador desde los *buckets* de
`ha01_adapter_latency_seconds` en `results/raw/*/api_metrics.txt`:

| Corrida | Llamadas | p95 adaptador | % llamadas > 120 ms |
| --- | ---: | ---: | ---: |
| `cache_opportunistic_b1_r1_sano` | 1566 | 116,5 ms | 3,70 % |
| `cache_blocking_b1_r1_sano` | 1525 | 115,2 ms | 3,67 % |
| **`cache_opportunistic_b1_r1_lento`** | **1441** | **472,3 ms** | **34,00 %** |

Las cifras de 111–117 ms sólo aparecen en las corridas cuyo estado degradado **era
`sano`**. `api_metrics.txt` es un **volcado final de contadores acumulados**: mezcla las
tres fases (120 s sana + 120 s degradada + 60 s recuperación). En una corrida con estado
degradado `lento`, dos tercios de las llamadas provienen de fases sanas y arrastran el
percentil hacia abajo.

**Consecuencia.** La observación §4.6 que el documento declara "incorrecta" era
**correcta**: con el proveedor lento el camino frío no cabe en el presupuesto de 120 ms,
y `EC-LAT-07` se incumple en el estado que precisamente materializa `EC-LAT-09`. La
refutación se apoyó en una cifra mal agregada.

Esto **no derriba la hipótesis HD-01** —el brazo C cumple el ASR de cotización
justamente porque *abandona* al agotar el presupuesto, que es el mecanismo bajo prueba—
pero invierte el sentido de un resultado publicado: no es que la dependencia quepa en
120 ms, es que **no cabe, y por eso hace falta el desacople**. Formulado así, incluso
refuerza el argumento del experimento.

**Corrección requerida:**
1. Recalcular el p95 del adaptador **por fase** y no sobre contadores acumulados.
2. Reescribir la fila `EC-LAT-07` del `EVALUACION_AVANCE_HA01.md` y restituir la
   observación §4.6 como válida.
3. Declarar `EC-LAT-07` como **incumplido con el proveedor lento/degradado y cumplido
   con el proveedor sano** — que es el resultado real y es más interesante.

---

### H-2 🟠 El estado `intermitente` no es intermitente: falla por cliente, no por petición

**Qué afirma el `EVALUACION_AVANCE_HA01.md` (§4, hallazgo nuevo nº 2):**

> Con fallos intermitentes del 30 %, el interruptor no llega a abrir en ningún brazo y
> aun así B incumple (1,10 %) y C cumple (0,00 %). Como el interruptor no interviene en
> ninguno de los dos, la diferencia es atribuible **sólo al desacople**. Es el argumento
> más fuerte del experimento, porque elimina la explicación alternativa.

**Qué muestra el código** (`provider/provider.py`):

```python
def _uniformes(customer_id: str) -> tuple[float, float]:
    d = hashlib.blake2b(f"{SEED}:{customer_id}".encode(), digest_size=16).digest()
    a = int.from_bytes(d[:8], "big") / 2**64
    b = int.from_bytes(d[8:], "big") / 2**64
    return ..., b

def muestrear_latencia(customer_id): 
    u, v = _uniformes(customer_id)
    return ..., v

# en el endpoint:
espera, v = muestrear_latencia(customer_id)
if FALLO_FRACCION and v < FALLO_FRACCION:   # v depende SOLO de customer_id
```

`v` se deriva por hash de `(SEED, customer_id)`. El fallo es por tanto **una propiedad
fija del cliente**: el 30 % de los clientes falla *siempre*, el 70 % restante *nunca*.
No hay ninguna aleatoriedad por petición.

El propio README declara esta decisión para la *latencia* (desviación 7, "el doble es
determinista por cliente, no por secuencia") y la justifica bien: hace las repeticiones
comparables. Pero **al reutilizar el mismo `v` para la decisión de fallo, la propiedad
se propaga a un sitio donde no es inocua.**

**Por qué importa.** El estado que el documento llama "proveedor que falla a medias" es
en realidad "subconjunto fijo y conocido de clientes cuyo perfil nunca se puede obtener".
Son dos modos de falla distintos:

- **El modelado (real):** el mismo cliente falla en todas sus peticiones. Su clave nunca
  se repuebla. Las peticiones fallidas se concentran en el 30 % del espacio de claves.
- **El descrito (intencionado):** cualquier petición tiene un 30 % de probabilidad de
  fallar. Un cliente que falla ahora puede acertar en el siguiente refresco.

El razonamiento de por qué el interruptor no abre —"ni diez fallos consecutivos ni el
50 % de la ventana"— depende del **entrelazado** de fallos y éxitos, y ese entrelazado
es distinto bajo los dos modelos. Con fallo por cliente y sorteo uniforme el resultado
probablemente se sostiene, pero **hoy es una coincidencia afortunada, no un control**.

**Corrección requerida.** Derivar la decisión de fallo de una uniforme independiente del
`customer_id` —por ejemplo un contador de petición o `random()` sin semilla por cliente—
y repetir las cuatro corridas `b5_intermitente`. Si el resultado se mantiene, el
hallazgo nº 2 queda blindado y es efectivamente el argumento más fuerte del experimento.
Si cambia, el hallazgo hay que reescribirlo. Mientras tanto, **declarar la limitación**:
el estado ejercita fallo persistente por cliente, no fallo aleatorio por petición.

---

### H-3 🟠 El brazo A "cumple" con proveedor caído tarifando sin ningún dato

**Qué muestra la tabla de HD-01.2** del `EVALUACION_AVANCE_HA01.md`:

| Estado | A | B | C |
| --- | ---: | ---: | ---: |
| caído | ✅ 0,00 % | ✅ 0,00 % | ✅ 0,00 % |

**Qué muestra la evidencia** (`resultados_por_fase.csv`, fase degradada):

| Corrida | p95 | > 475 ms | **% con respaldo** |
| --- | ---: | ---: | ---: |
| `direct_b1_r1_caido` | 64,4 ms | 0,00 % | **98,89 %** |
| `direct_b1_r1_sin_respuesta` | 64,9 ms | 4,26 % | **99,43 %** |
| `cache_blocking_b1_r1_caido` | 64,3 ms | 0,00 % | 3,95 % |
| `cache_opportunistic_b1_r1_caido` | 64,3 ms | 0,00 % | 3,67 % |

El brazo A no tiene caché (`USA_CACHE["direct"] = False`). Cuando el interruptor abre,
`brazo_directo` devuelve `PERFIL_DEFECTO` (`strategies.py:83`) sin posibilidad de
*último valor conocido*. El ✅ de A con proveedor caído significa: **el 98,9 % de las
cotizaciones se tarifica con el perfil por defecto, con cero señal de Open Finance**.

B y C, en la misma celda, resuelven el ~96 % desde caché con datos reales y usan
respaldo sólo en el ~4 %.

**Por qué importa.** Poner ✅ en las tres columnas de esa fila sugiere equivalencia
arquitectónica donde hay una diferencia enorme en la calidad de la tarifa. El propósito
declarado de HA-01 no es "responder rápido" sino "proteger el presupuesto de latencia
**sin** destruir la calidad de la tarifa" — el diseño lo dice explícitamente en el
criterio de refutación del Anexo B:

> Se refuta la hipótesis si el brazo C alcanza el umbral **sólo degradando la proporción
> de valor de respaldo a un nivel que actuaría considere inaceptable**.

Ese criterio se aplica a C pero no se aplicó a A al declararlo conforme. Con el criterio
del propio diseño, **A con proveedor caído es el ejemplo canónico de "cumple la latencia
por un camino inaceptable"**.

**Corrección requerida.** La tabla de HD-01.2 debe llevar la columna `% con respaldo`
junto al veredicto, o el ✅ de A en `caído`/`sin respuesta` debe marcarse como
*cumple latencia, incumple calidad del dato*. Es una corrección de presentación, no de
medición: el dato ya está en el CSV.

> **Nota.** Esto refuerza una conclusión que la evaluación ya insinúa pero no remata: el
> veredicto de HA-01 no puede leerse sobre el eje de latencia solo. La **proporción con
> respaldo es la segunda medida de respuesta de `EC-LAT-09`**, tal como el propio
> documento propone en su §7 punto 5. Conviene elevarlo de recomendación a conclusión.

---

### H-4 🟡 La evidencia del estado inyectado no existe en ninguna corrida

`scripts/_corrida.sh` restaura el estado sano en la línea 144 (fase de recuperación) y
captura `toxiproxy.json` en la línea 166, **después**. Resultado: las 52 corridas
archivan `{"...","toxics":[]}`, incluidas las de estado `lento`, `degradado`,
`sin_respuesta` y `caido`.

Verificado sobre las cinco corridas del bloque 1: idéntico en todas.

El README presenta `toxiproxy.json` como *"toxinas activas, para confirmar el estado
inyectado"* y lo lista entre lo que hace un resultado **auditable seis semanas después**.
Hoy no confirma nada.

**No invalida los resultados** —el estado efectivo se corrobora indirectamente por las
latencias observadas y por `provider_metrics.txt`— pero el artefacto de evidencia que el
protocolo designó para esto está vacío.

**Corrección:** capturar `toxiproxy.json` inmediatamente después de `states.sh
"${ESTADO}"` (línea 141), o capturar dos instantáneas (`toxiproxy_degradado.json` y
`toxiproxy_final.json`).

---

### H-5 🟡 Las cifras de `EC-LAT-07` no son reproducibles desde el pipeline

`scripts/analizar.py` no contiene ninguna referencia a `ha01_adapter_latency_seconds`
(verificado por búsqueda). El CSV consolidado no tiene columna de latencia del adaptador.
Las cifras de 111–117 ms del `EVALUACION_AVANCE_HA01.md` se obtuvieron por un cálculo
ad-hoc que no quedó registrado — y que, según H-1, estaba mal agregado.

Es la causa raíz de H-1: lo que no pasa por el pipeline no pasa por sus controles.

**Corrección:** añadir `p95_adapter_ms` y `pct_adapter_sobre_120ms` como columnas por
fase en `resultados_por_fase.csv`. `EC-LAT-07` es una restricción arquitectónica
declarada en la hoja de trabajo; merece estar en el consolidado y no en una nota.

---

## 4. Cobertura del diseño: qué se ejecutó y qué no

| Elemento del diseño | Estado | Observación de la auditoría |
| --- | :---: | --- |
| Brazos A / B / C / C′ | ✅ | Mismo binario, `QUOTE_STRATEGY`. Control correcto |
| 5 estados del proveedor | ✅ | Más `intermitente`, añadido con buen criterio (ver H-2 sobre su implementación) |
| Tasas de acierto 99/96/90/50 % | ✅ | Se añadió el 98 %, que localiza el cruce de B entre 96 y 98 %. Buena decisión |
| Políticas de interruptor × tráfico | ✅ | Corregido su emplazamiento: se miden en B, donde discriminan. Ver §5 |
| Coalescencia C vs C′ | ✅ | Requirió la celda `estampida_ttl2`; sin ella hubo 0 coalescencias. Bien diagnosticado |
| Tasa de llegada 20/50/100/200 | ✅ | Bloque 4, añadido. El diseño la declaraba independiente sin variarla nunca |
| **3 corridas contrabalanceadas (cuadrado latino)** | ❌ | **Se ejecutó 1 repetición.** Ver §5 |
| Verificación de equivalencia de contrato | ⚠️ | El "control crítico" del Anexo A. Garantizado por construcción (mismo binario), pero no hay verificación automática previa a cada corrida como el diseño pide |
| `EC-LAT-07` (≤ 120 ms/dependencia) | ❌ | Declarado cumplido sobre cifras mal agregadas. Ver H-1 |
| `EC-LAT-08` (timeout duro 700 ms) | ✅ | Verificado en `adapter.py` y en los p95 de camino (~700-795 ms) |

---

## 5. Sobre las desviaciones que el equipo sí declaró

Dos merecen juicio de auditoría, porque son las que más podrían objetarse.

### Una repetición en vez de tres (desviación 18) — **aceptable, bien justificada**

El Anexo B exige explícitamente las tres corridas ("en **las tres corridas**"). Se
ejecutó una, salvo en la celda cercana al umbral.

**La justificación es sólida y la auditoría la respalda con los datos:** la varianza
entre corridas independientes es minúscula (p95 de 64,8–64,9 ms en seis corridas), y la
celda que de verdad decide —B con proveedor lento, al 1,28 % contra el 1 % permitido—
**sí tiene tres réplicas**: 1,28 %, 1,15 % y 1,24 %. Esa dispersión (σ ≈ 0,07 puntos)
deja el incumplimiento de B fuera de toda duda razonable, que es donde importaba gastar
las repeticiones.

Que el contrabalanceo pierda sentido con n=1 es cierto, y el riesgo de efecto de orden
queda mitigado porque cada corrida reinicia la API, vacía Redis y restablece el
proveedor. **Es una desviación bien razonada, no un atajo.** Debe constar en el informe
final como tal.

### Las políticas del interruptor se miden en B y no en C — **es una mejora, no una desviación**

El diseño asignaba el punto de sensibilidad 4 al brazo C. En C las cuatro celdas cumplen
con holgura porque ninguna petición espera más que el presupuesto: la política del
interruptor es **invisible** al percentil. Al correrlas en B aparece el incumplimiento
(conteo + tráfico bajo → 1,19 % sobre 475 ms y p99 de 716 ms).

Esto **rescata** el punto de sensibilidad 4, que tal como estaba diseñado no habría
decidido nada. Es el tipo de corrección que justifica ejecutar un experimento en vez de
razonarlo en papel. Verificado en el CSV: `cache_blocking_b3b_pol_count_bajo` abre a los
15 s frente a los 5 s de la política por conteo con tráfico alto.

---

## 6. Conclusiones arquitectónicas que la evidencia sostiene

Tras la auditoría, esto es lo que puede afirmarse **con respaldo en los datos**:

1. ✅ **El desacople oportunista protege el presupuesto de latencia.** Sostenido. El
   brazo C mantiene 0,00 % sobre 475 ms en los seis estados del proveedor, con p99
   acotado por presupuesto + tarifa (~190 ms) **independientemente de la tasa de
   acierto**. Es el resultado central de HA-01 y está bien demostrado.

2. ✅ **El interruptor y el desacople hacen cosas distintas.** Sostenido, y es el
   hallazgo más valioso del experimento. Frente a un proveedor **caído** el interruptor
   basta y rescata también a la caché simple; frente a un proveedor **lento** el
   interruptor nunca abre y sólo el desacople cumple. Obliga a reescribir §1.2.4 de la
   hoja de trabajo semana 5, que hoy atribuye todo el mérito a la actualización
   oportunista sin separar ambos mecanismos.
   ⚠️ *Con la salvedad de H-2:* la pata `intermitente` de este argumento necesita
   repetirse con fallo aleatorio por petición.

3. ⚠️ **HD-01.3 se refuta en su forma publicada.** El diseño predecía que el camino
   degradado sería más rápido que el frío. Sólo ocurre con el interruptor abierto. Con
   proveedor **lento** —donde nunca abre— el degradado cuesta 189 ms contra 159 ms del
   frío: **más lento**. La evaluación ya lo recoge correctamente. El Anexo G (110/210 ms)
   debe rehacerse.

4. ❌ **HD-01.4 se refuta y debe reescribirse.** En C la tasa de acierto no decide el
   percentil; decide la **proporción con respaldo** (≈ 1 − acierto). Quien depende del
   acierto es B, con su mínimo alrededor del 97 %. La redacción propuesta por el equipo
   es correcta, y su advertencia sobre la segunda cláusula —"respaldo ≤ 5 %" equivale a
   "acierto ≥ 95 %", es aritmética y no un resultado— es una observación fina y acertada.

5. ✅ **`EC-LAT-02` (horario pico) se cumple.** Latencia plana de 20 a 200 sol/s: p95 de
   65 ms y p99 entre 138 y 149 ms en los cuatro escalones. Verificado en el CSV.

6. ❌ **`EC-LAT-07` no se cumple con el proveedor degradado.** Ver H-1. Es una corrección
   al alza del valor del experimento, no a la baja.

7. ⚠️ **El veredicto de HA-01 no puede leerse sólo en el eje de latencia.** La
   proporción con respaldo debe ser medida de respuesta de primera clase en `EC-LAT-09`.
   Ver H-3. **Y sigue faltando el número que decide:** cuánto respaldo considera
   aceptable actuaría. Sin él, C gana por definición y el criterio de refutación del
   Anexo B es inaplicable. Es la brecha más importante que queda abierta, y no se cierra
   con más corridas.

---

## 7. Acciones requeridas antes de publicar el informe

**Bloqueantes:**

1. **H-1** — Recalcular el p95 del adaptador por fase; corregir el veredicto de
   `EC-LAT-07`; restituir la observación §4.6 como válida.
2. **H-3** — Añadir `% con respaldo` a la tabla de HD-01.2 o matizar el ✅ del brazo A.

**Importantes:**

3. **H-2** — Repetir las cuatro corridas `b5_intermitente` con fallo independiente del
   `customer_id`; hasta entonces, declarar la limitación junto al hallazgo nº 2.
4. **H-5** — Llevar la latencia del adaptador al CSV consolidado.

**Menores:**

5. **H-4** — Mover la captura de `toxiproxy.json` antes de la fase de recuperación.
6. Declarar en el Anexo D las dos amenazas que el equipo ya identificó y aún no trasladó:
   el motor de tarifa es casi todo espera (`RATING_CPU_ITERS=1200` ≈ décimas de ms de CPU
   real) y no reproduce la competencia por CPU de un motor de reglas real.

**Trazabilidad pendiente** (ya identificada por el equipo, sigue abierta):

7. `Estrategia-de-pruebas.md` asocia `EC-LAT-09` a **HA-07** y el diseño lo asocia a
   **HA-01**. Reconciliar en Jira.
8. El Anexo B dice "los cuatro estados" cuando el modelo define cinco (hoy seis con
   `intermitente`); el Anexo F lista "HD-01.1 a HD-01.7" habiendo ocho sub-hipótesis.
   La incoherencia está también en la wiki.

---

## 8. Valoración final

La ejecución **permite concluir lo que se quería validar arquitectónicamente**: la
respuesta que la hoja de trabajo semana 5 da a la pregunta 3 del enunciado queda
respaldada por evidencia, y además **corregida en un punto sustantivo** —la separación
entre lo que aporta el interruptor y lo que aporta el desacople—, que es exactamente lo
que se le pide a un experimento de arquitectura.

No se detectó ofuscación de decisiones. Al contrario: el nivel de autocrítica declarada
—21 desviaciones documentadas con su evidencia, incluida una nota de trazabilidad sobre
un cambio de política que no se aplicó cuando se dijo— está por encima de lo habitual y
es lo que hizo posible esta auditoría.

Los defectos encontrados son de **agregación y de presentación**, no de diseño
experimental ni de implementación: el código de los cuatro brazos, del adaptador y del
interruptor es correcto y hace lo que la hipótesis afirma. H-1 y H-3 se corrigen
reescribiendo conclusiones sobre datos ya recogidos; sólo H-2 requiere volver a correr,
y son cuatro corridas de unos 30 minutos.

**Recomendación: publicar tras las correcciones 1 y 2, con H-2 declarado como limitación
si no da tiempo a repetir las corridas.**
