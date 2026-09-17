# Auditoría de seguimiento — verificación de las correcciones de HA-01

_Segunda pasada de auditoría. Verifica si las cinco acciones exigidas por
`AUDITORIA_HA01.md` se ejecutaron realmente, y si lo hicieron bien._

| | |
| --- | --- |
| **Objeto auditado** | Las correcciones aplicadas a `experimentos/ha01/` tras la primera auditoría |
| **Estado del experimento** | **56 corridas** (52 originales + 4 nuevas `b5b_intermitente`) |
| **Contra qué se verifica** | Los cinco hallazgos H-1 … H-5 de `AUDITORIA_HA01.md` |
| **Fecha** | 17/09/2026 |
| **Método** | Lectura del código corregido; recálculo independiente del p95 del adaptador por fase; contraste de las corridas `b5_*` (antes) contra `b5b_*` (después); verificación de que cada cifra citada en los documentos sale del CSV consolidado |

---

## 1. Veredicto

**Las cinco correcciones se aplicaron, y las cinco están bien hechas.** No hay
correcciones cosméticas ni declaradas-pero-no-ejecutadas: cada una toca el código o el
pipeline, no sólo el texto.

Lo más relevante es que **la corrección de H-2 exigía volver a correr, se corrió, y el
resultado confirma la conclusión original** — que es el desenlace que más credibilidad
da al experimento, porque el equipo se expuso a que la repetición lo refutara.

| Hallazgo | Acción exigida | Estado | Verificación de esta auditoría |
| --- | --- | :---: | --- |
| **H-1** 🔴 | Recalcular `EC-LAT-07` por fase; corregir el veredicto | ✅ **Resuelto** | Recalculado por fase: 495,6 ms / 99,78 % con proveedor lento. El veredicto se invirtió a ❌ y la observación §4.6 quedó restituida |
| **H-2** 🟠 | Repetir `b5_intermitente` con fallo por petición | ✅ **Resuelto y confirmado** | Código corregido (`_uniforme_peticion`); 4 corridas nuevas; el resultado **se mantiene** |
| **H-3** 🟠 | Añadir `% con respaldo` a la tabla de HD-01.2 | ✅ **Resuelto** | Tabla nueva con las tres columnas; el ✅ de A queda matizado y la brecha actuarial declarada |
| **H-4** 🟡 | Capturar el estado del proxy antes de la recuperación | ✅ **Resuelto** | `toxiproxy_degradado.json` se captura en la línea 146, con las toxinas puestas |
| **H-5** 🟡 | Llevar la latencia del adaptador al CSV | ✅ **Resuelto** | `analizar.py` calcula `p95_adapter_ms` y `pct_adapter_sobre_120ms` por fase; ambas están en el CSV |

**Queda un defecto residual menor** (D-1, §4): una fila del `EVALUACION_AVANCE_HA01.md`
sigue describiendo el mecanismo viejo de fallas intermitentes, el que H-2 declaró
inválido. Es una línea de texto, no un resultado.

---

## 2. Verificación por hallazgo

### H-1 ✅ `EC-LAT-07` — resuelto, y la corrección fue más lejos que la exigida

La primera auditoría pedía recalcular por fase. Se hizo, **y de paso se corrigió un
error de la propia auditoría**: sus tres filas de evidencia seguían siendo cifras *por
corrida*, es decir todavía acumuladas. La rectificación del 16/09 lo señala
explícitamente («esta auditoría diagnosticó bien el defecto pero no lo corrigió del todo
en su propia evidencia»).

Recalculé de forma independiente desde el CSV consolidado, que ahora trae las columnas:

| Corrida | Fase | n llamadas | p95 adaptador | % > 120 ms |
| --- | --- | ---: | ---: | ---: |
| `cache_opportunistic_b1_r1_sano` | sana | 501 | 116,0 ms | 3,02 % |
| `cache_opportunistic_b1_r1_sano` | degradada | 512 | **121,8 ms** | 5,12 % |
| `cache_opportunistic_b1_r1_lento` | degradada | 452 | **495,6 ms** | **99,78 %** |
| `cache_blocking_b1_r1_lento` | degradada | 469 | **490,3 ms** | **99,14 %** |
| `cache_opportunistic_b1_r1_degradado` | degradada | 32 | **984,5 ms** | 96,88 % |
| `cache_opportunistic_b5b_intermitente_rate` | degradada | 927 | **948,9 ms** | 31,88 % |

Coincide con lo publicado. El veredicto del `EVALUACION_AVANCE_HA01.md` pasó de
«✅ cumple con poco margen» a «❌ **se incumple con el proveedor degradado**», la fila
§4.6 pasó de «❌ incorrecta» a «✅ **válida** (rectificado)», y el documento conserva la
nota de que una versión anterior afirmaba lo contrario. **La trazabilidad del error está
preservada, que es lo correcto en un informe académico.**

Dos observaciones que la corrección hace visibles y que conviene no perder:

- **Con el proveedor sano, la fase degradada ya está en 121,8 ms**: `EC-LAT-07` está al
  filo incluso sin degradación. El presupuesto de 120 ms no tiene margen real.
- **La celda `degradado` tiene n=32 llamadas** frente a las ~450 de las demás. Es
  coherente con que el interruptor abra a los 7 s y corte el resto, pero significa que
  su p95 de 984,5 ms descansa sobre una muestra pequeña. No afecta al veredicto —el
  incumplimiento se sostiene en `lento`, que tiene n=452— pero merece una nota si esa
  cifra se cita aislada.

### H-2 ✅ El estado intermitente — corregido en el código, repetido, y **confirmado**

**El código está bien corregido.** `provider.py` ahora separa las dos uniformes:

```python
def _uniforme_cliente(customer_id) -> float:     # latencia: sigue por cliente
    d = blake2b(f"{SEED}:{customer_id}")...

_SECUENCIA = itertools.count()
def _uniforme_peticion() -> float:               # fallo: por PETICION
    n = next(_SECUENCIA)
    d = blake2b(f"{SEED}:peticion:{n}")...
```

La decisión es correcta en los dos ejes: el fallo se desacopla del cliente (que era el
defecto), y la latencia **sigue** siendo determinista por cliente, con lo que se conserva
la propiedad de la desviación 7 que hacía comparables las repeticiones. Usar un contador
en vez de `random()` mantiene la reproducibilidad dada la secuencia de llegada. El
comentario del código explica por qué, con el nivel de detalle del resto del montaje.

**Las cuatro corridas nuevas son válidas.** `sanidad.txt` de las cuatro: todas las
verificaciones pasan, acierto 0,9601–0,9619 contra 0,96 objetivo, lag del bucle 4,0–4,3 ms,
0 parones.

**El resultado se mantiene** — contraste directo:

| Brazo | Mecanismo | Corrida | > 475 ms | p99 | ¿Abre el interruptor? |
| --- | --- | --- | ---: | ---: | :---: |
| B | por cliente (viejo) | `b5_intermitente_rate` | ❌ 1,101 % | 709,2 ms | No |
| B | por cliente (viejo) | `b5_intermitente_count` | ❌ 1,163 % | 714,0 ms | No |
| **B** | **por petición (nuevo)** | `b5b_intermitente_rate` | ❌ **1,218 %** | 717,9 ms | No |
| **B** | **por petición (nuevo)** | `b5b_intermitente_count` | ❌ **1,247 %** | 719,8 ms | No |
| C | por cliente (viejo) | `b5_intermitente_rate` | ✅ 0,000 % | 178,4 ms | No |
| **C** | **por petición (nuevo)** | `b5b_intermitente_rate` | ✅ **0,000 %** | 178,0 ms | No |
| **C** | **por petición (nuevo)** | `b5b_intermitente_count` | ✅ **0,000 %** | 178,3 ms | No |

El interruptor **no abre en ninguna de las ocho corridas** (`breaker_max = 0`), bajo los
dos mecanismos y las dos políticas. Esa es la premisa de la que depende todo el
argumento, y ahora está verificada sobre el modelo de falla correcto.

**Consecuencia para la conclusión.** El hallazgo nº 2 —«como el interruptor no interviene
en ninguno de los dos brazos, la diferencia es atribuible **sólo al desacople**»— queda
**blindado**. Era el punto donde la primera auditoría dijo que la conclusión se sostenía
«por coincidencia afortunada, no por control». Ahora es control.

Desde el punto de vista de la validez interna, es el resultado más importante de esta
segunda pasada: elimina la explicación alternativa del efecto medido, que es
exactamente lo que un experimento de arquitectura debe hacer.

### H-3 ✅ La tabla de HD-01.2 — resuelto, y mejor de lo pedido

La auditoría pedía añadir la columna de respaldo *o* matizar el ✅. Se hizo una tabla
completa de proporción con respaldo junto a la de latencia:

| Estado | A | B | C |
| --- | ---: | ---: | ---: |
| degradado | **98,94 %** | 3,43 % | 4,01 % |
| sin respuesta | **99,43 %** | 3,81 % | 3,82 % |
| caído | **98,89 %** | 3,95 % | 3,67 % |

Verificado contra `resultados_por_fase.csv`: las seis cifras coinciden.

Y se sacó la conclusión que la primera auditoría sólo insinuaba: la proporción con
respaldo es **segunda medida de respuesta de `EC-LAT-09`**, no una nota al margen, con
la brecha actuarial declarada en un recuadro propio («sin ese número, C gana por
definición y el criterio de refutación del Anexo B es inaplicable»).

Es la corrección de mayor valor arquitectónico de las cinco, porque cambia cómo se lee
el veredicto de HA-01: no como un resultado de latencia, sino como un intercambio entre
latencia y calidad del dato con que se tarifica.

### H-4 ✅ Evidencia del estado inyectado — resuelto

`_corrida.sh:146` captura `toxiproxy_degradado.json` inmediatamente después de aplicar
el estado y **antes** de la fase de recuperación. Se conservan las dos instantáneas, con
un comentario que explica que `toxiproxy.json` documenta el final y no el estado bajo
prueba.

**Una aclaración necesaria para quien audite después.** En las cuatro corridas `b5b_*`,
`toxiproxy_degradado.json` trae igualmente `"toxics":[]` — y **es correcto**: el estado
`intermitente` no se inyecta con Toxiproxy sino en el doble del proveedor
(`POST /modo?fallo_fraccion=0.3`), por la razón que el propio equipo documentó: la
`toxicity` de Toxiproxy se aplica por conexión y el pool persistente de `httpx` habría
dejado la fracción real fuera de control.

La evidencia de ese estado vive por tanto en el lado del doble
(`ha01_provider_colgadas`), no en el proxy. **Conviene archivar también la respuesta de
`GET /modo` del doble** en las corridas de estado `intermitente`, para que el artefacto
que prueba el estado inyectado exista para los seis estados y no sólo para los cinco de
Toxiproxy. Es el mismo criterio que motivó H-4.

### H-5 ✅ Reproducibilidad — resuelto en la raíz

`analizar.py` calcula ahora, por fase y desde Prometheus:

- `llamadas_adapter`
- `p95_adapter_ms` — vía `histogram_quantile` sobre `increase(...)` acotado a la fase
- `pct_adapter_sobre_120ms` — por **conteo directo** del bucket `le="0.12"`, no por
  interpolación, aprovechando que hay frontera de bucket exacta justo en el umbral de
  `EC-LAT-07`

Las tres columnas están en `resultados_por_fase.csv`. Verificado que los valores
publicados se reproducen desde el CSV.

Ese detalle del conteo directo es correcto y no trivial: `histogram_quantile` habría
interpolado dentro del bucket y dado un porcentaje aproximado justo en la cifra que
decide el cumplimiento de una restricción arquitectónica.

Con esto, **la causa raíz de H-1 queda cerrada**: la métrica que sostiene `EC-LAT-07`
pasa por el pipeline y por sus controles, en vez de calcularse a mano.

---

## 3. Efecto sobre las conclusiones arquitectónicas

Ninguna conclusión central cambió; dos se reforzaron y una se invirtió.

| Conclusión | Antes de las correcciones | Después |
| --- | --- | --- |
| El desacople oportunista protege el presupuesto de latencia | ✅ Sostenida | ✅ **Sin cambios.** C mantiene 0,00 % sobre 475 ms en los seis estados |
| Interruptor y desacople hacen cosas distintas | ✅ Sostenida, con salvedad en la pata `intermitente` | ✅ **Reforzada.** La salvedad desapareció: repetida con el modelo de falla correcto, se mantiene |
| `EC-LAT-07` (≤ 120 ms por dependencia) | ✅ «cumple con poco margen» | ❌ **Invertida.** Se incumple con proveedor lento (99,78 % fuera de presupuesto) y está al filo con proveedor sano (121,8 ms) |
| El veredicto de HA-01 no se lee sólo en latencia | ⚠️ Insinuada | ✅ **Elevada a conclusión**, con la proporción con respaldo como segunda medida de `EC-LAT-09` |

**La inversión de `EC-LAT-07` no debilita el experimento: lo fortalece.** El argumento
publicado pasa de «la dependencia cabe en el presupuesto» a «**no cabe, y por eso hace
falta el desacople**». La segunda formulación es la que justifica arquitectónicamente la
táctica bajo prueba, y ahora está respaldada por la medición en vez de contradicha por
ella.

---

## 4. Defecto residual

### D-1 🟡 Una fila del `EVALUACION_AVANCE_HA01.md` describe el mecanismo ya invalidado

`EVALUACION_AVANCE_HA01.md:26` sigue diciendo:

> | §4.3 Falta el estado de fallas intermitentes | ✅ válida · mecanismo corregido | … Se
> implementó en el doble, **por petición y por hash del cliente** |

«Por hash del cliente» es precisamente el defecto que H-2 identificó y que el código ya
no hace. La fila describe el mecanismo viejo. El §4 del mismo documento cuenta la
historia correcta (líneas 253–266, con la tabla de contraste `b5` contra `b5b`), así que
es una inconsistencia interna, no un error de resultado.

**Corrección:** reescribir esa celda como *«Se implementó en el doble, **por petición**;
una primera versión lo derivaba del hash del cliente y se corrigió — ver §4»*.

### D-2 🟡 Las correcciones no están en el registro de desviaciones del README

El `README.md` mantiene las 21 desviaciones numeradas como registro de todo lo que se
apartó de los documentos publicados, y declara que «todas deben quedar registradas en el
informe». Las correcciones de esta ronda —el fallo por petición del estado intermitente,
la doble captura del proxy, la latencia del adaptador por fase— **no aparecen** ahí.

Son exactamente el tipo de cambio que ese registro existe para capturar, y el más
importante de los tres (el mecanismo de fallo intermitente) cambia cómo debe
interpretarse un estado del modelo de fallas.

**Corrección:** añadir las desviaciones 22, 23 y 24 al README con su evidencia, igual
que las 21 anteriores.

---

## 5. Acciones pendientes

**Del seguimiento (nuevas):**

1. **D-1** — Corregir la fila 26 del `EVALUACION_AVANCE_HA01.md`.
2. **D-2** — Registrar las tres correcciones como desviaciones 22–24 del README.
3. Archivar `GET /modo` del doble en las corridas de estado `intermitente` (cierra H-4
   para los seis estados).
4. Añadir una nota a la celda `degradado` de la tabla de `EC-LAT-07`: n=32 llamadas, el
   interruptor corta el resto.

**Heredadas de la primera auditoría, aún abiertas:**

5. Declarar en el Anexo D que el motor de tarifa es casi todo espera
   (`RATING_CPU_ITERS=1200` ≈ décimas de ms de CPU real) y no reproduce la competencia
   por CPU de un motor de reglas real.
6. Reconciliar en Jira el identificador: `Estrategia-de-pruebas.md` asocia `EC-LAT-09` a
   **HA-07**, el diseño lo asocia a **HA-01**.
7. Unificar el conteo de estados —el Anexo B dice «los cuatro», el modelo define seis con
   `intermitente`— y el de sub-hipótesis —el Anexo F lista «HD-01.1 a HD-01.7» habiendo
   ocho.
8. Rehacer el **Anexo G** con los valores medidos (predecía 110 ms para el camino
   degradado y 210 ms para el frío; el frío cuesta ~160 ms y el degradado depende del
   interruptor).
9. Reescribir **§1.2.4 de la hoja de trabajo semana 5**, que atribuye todo el mérito a la
   actualización oportunista sin separar qué hace el interruptor y qué hace el desacople.

**Sin cerrar, y no se cierra con corridas:**

10. **El umbral de respaldo que actuaría considera aceptable.** Es la brecha que impide
    aplicar el criterio de refutación del Anexo B. Sigue siendo la pieza que falta para
    que el veredicto de HA-01 sea completo.

---

## 6. Valoración

Las cinco correcciones se ejecutaron sobre el código y el pipeline, no sobre el texto.
Dos detalles distinguen este trabajo del cumplimiento formal de una lista:

**Se corrigió un error de la propia auditoría.** La rectificación de H-1 señala que las
cifras de evidencia de `AUDITORIA_HA01.md` seguían siendo por corrida y por tanto
acumuladas. La auditoría diagnosticó bien y se equivocó al ilustrarlo; el equipo lo
detectó y lo dejó escrito en vez de silenciarlo.

**Se repitió una medición que podía refutar la conclusión propia, y se publicó el
contraste.** La tabla `b5` contra `b5b` del `EVALUACION_AVANCE_HA01.md` muestra los dos
mecanismos lado a lado. Si el resultado hubiera cambiado, la tabla lo habría mostrado
igual. Que se mantenga —B incumple con 1,22–1,25 %, C cumple con 0,00 %, el interruptor
no abre en ninguna de las ocho corridas— convierte el hallazgo nº 2 de coincidencia en
control experimental.

El defecto residual D-1 es una frase desactualizada y D-2 una omisión de registro.
Ninguno afecta a un resultado.

**Recomendación: el experimento está listo para publicarse** una vez corregidos D-1 y
D-2, que son media hora de trabajo documental. La brecha actuarial (punto 10) debe
declararse explícitamente como límite del alcance, no resolverse: es una decisión de
negocio, no de arquitectura.
