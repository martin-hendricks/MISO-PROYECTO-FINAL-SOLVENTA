# Diseño de experimento

**Módulo 4 — EDA**
**Maestría en Ingeniería de Software — MISW4501 Arquitectura de Software**
**Caso de estudio:** Solventa — plataforma insurtech
**Versión:** 1.0

> **Documento complementario:** la implementación detallada (Docker, esquemas de base de datos, código fuente, scripts de carga y protocolo de ejecución) se encuentra en `Guia_Tecnica_HA-08.md`.

---

## 1. Ficha del experimento

| Campo | Detalle |
|---|---|
| **Título del experimento** | Modelo de lectura de baja latencia para el estado de siniestro mediante CQRS con proyección materializada y caché |
| **Propósito del experimento** | Evaluar si las tácticas de latencia propuestas para la consulta de estado de siniestro —desacoplar el modelo de lectura del de escritura, materializar una proyección desnormalizada y servirla desde un almacén en memoria— permiten cumplir el ASR EC-LAT-11 (p95 ≤ 150 ms), y determinar cuál es el **nivel mínimo de complejidad** que lo satisface. |
| **Resultados esperados** | Se espera que la lectura directa sobre el modelo transaccional normalizado **no** alcance el umbral bajo la carga de operación regular, que la proyección materializada reduzca el p95 de forma sustancial, y que el caché en memoria aporte una mejora adicional. El experimento debe además cuantificar el costo de esas tácticas en términos de *staleness* (lag de proyección) para determinar si la consistencia eventual resultante es aceptable para el escenario. |
| **Elementos de arquitectura involucrados** | **ASR asociado:** EC-LAT-11 — Latencia, prioridad (A,A).<br>**Historia de arquitectura:** HA-08.<br>**Vistas y modelos:** Vista funcional (modelo de componentes: API de consulta, proyector, almacenes de lectura y escritura); Vista de información (modelo de datos: esquema transaccional vs. proyección); Vista de despliegue (modelo de contenedores).<br>**Puntos de sensibilidad que se desean probar:** separación del modelo de lectura, política de caché (TTL e invalidación) y tasa de llegada de consultas. |
| **Esfuerzo estimado** | Tiempo: 1,5 semanas — 60 horas<br>Horas hombre: 15 horas/hombre (4 integrantes) |

### Recursos requeridos

Lista de recursos requeridos para ejecutar el experimento (software, librerías, hardware):

- **Lenguaje y framework:** Python 3.12, FastAPI, Uvicorn
- **Contenerización:** Docker y Docker Compose V2
- **Almacenamiento:** PostgreSQL 16 (modelo transaccional y proyección), Redis 7 (caché)
- **Mensajería:** Redpanda (API compatible con Kafka)
- **Librerías:** `asyncpg`, `redis-py` (asyncio), `aiokafka`, `orjson`, `pydantic`, `prometheus-client`
- **Generación de carga:** k6
- **Observabilidad:** Prometheus, Grafana
- **Hardware:** estación de desarrollo con mínimo 16 GB de RAM, 4 núcleos y 20 GB de disco libre (el dataset sintético ocupa ~2 GB más índices)

---

## 2. Hipótesis de diseño

### Enunciado

> **Si** separamos el modelo de lectura del de escritura mediante CQRS, materializando el estado del siniestro en una proyección desnormalizada (un registro autocontenido por siniestro) mantenida de forma asíncrona por un proyector que consume los eventos de dominio del proceso de evaluación, y servimos esa proyección desde un almacén clave-valor en memoria con *fallback* a la proyección persistente,
>
> **entonces** la consulta de estado de siniestro alcanzará un **p95 ≤ 150 ms** bajo la carga esperada en producción regular,
>
> **aceptando como contrapartida** consistencia eventual acotada (*lag* de proyección p95 ≤ 2 s), duplicación de datos y mayor complejidad operativa.

| Campo | Detalle |
|---|---|
| **Historia de arquitectura asociada** | HA-08 — Modelo de lectura de baja latencia para el estado de siniestro |
| **Escenario de calidad** | EC-LAT-11 — Latencia, prioridad (A,A), clasificado como ASR |
| **Nivel de incertidumbre** | **Medio-Alto.** El equipo tiene experiencia previa con CQRS, pero desconoce (a) si la proyección por sí sola basta o si el caché es indispensable, (b) cuánto lag introduce el proyector bajo carga concurrente de lectura, y (c) cuál es el punto de quiebre de cada alternativa. El costo de equivocarse es alto: revertir CQRS una vez adoptado implica reescribir el camino de lectura y el proceso de evaluación completo. |

### Puntos de sensibilidad

| # | Punto de sensibilidad | ¿Qué probar? |
|---|---|---|
| 1 | **Grado de separación del modelo de lectura.** Es la decisión arquitectónica central: cuánta separación entre comando y consulta se requiere para satisfacer el ASR. | Variar la estrategia de lectura en tres niveles: **A** lectura directa sobre el modelo transaccional normalizado (sin separación), **B** proyección materializada persistente (separación lógica y física del esquema), **C** proyección + caché en memoria (separación con copia adicional en otro medio de almacenamiento). |
| 2 | **Política del caché.** Determina el balance entre latencia y *staleness*, que es el trade-off que la historia HA-08 pone en tensión: el cliente quiere inmediatez, pero también quiere ver el estado *vigente*. | Variar el TTL del caché: 0 s (sin caché, equivale al brazo B), 30 s (valor propuesto) y 300 s. Medir simultáneamente el p95 y el lag observado por el cliente. |
| 3 | **Tasa de llegada de consultas.** Identifica el margen de crecimiento de cada alternativa antes de incumplir el ASR. | Escalones de 10, 25, 50 y 80 solicitudes por segundo, registrando el p95 en cada escalón para localizar el punto de quiebre de cada brazo. |

### Sub-hipótesis verificables

| ID | Enunciado | Punto de sensibilidad | Brazo que la prueba |
|---|---|---|---|
| HD-08.1 | La lectura directa sobre el modelo transaccional normalizado **no** alcanza el p95 objetivo bajo la carga de operación regular | 1 | A |
| HD-08.2 | La proyección materializada desnormalizada reduce el p95 en al menos un 60 % respecto a la línea base | 1 | B |
| HD-08.3 | El caché en memoria aporta una reducción adicional significativa sobre la proyección persistente | 1, 2 | C vs. B |
| HD-08.4 | El *lag* de proyección se mantiene acotado (p95 ≤ 2 s) mientras el sistema atiende la carga de lectura | 2 | B, C |

> **Nota metodológica.** HD-08.3 es genuinamente refutable. Si el brazo B ya cumple el umbral, el caché es complejidad no justificada y el informe debe recomendar la arquitectura más simple que satisface el ASR, no la más sofisticada que se probó. Un experimento que sólo puede confirmar la solución preferida no aporta información arquitectónica.

---

## 3. Estilos de arquitectura asociados al experimento

| Estilo de arquitectura asociado al experimento | Análisis (atributos de calidad que favorece y desfavorece) |
|---|---|
| **CQRS (segregación de responsabilidades de comando y consulta)** | **Favorece:**<br>• Latencia de lectura<br>• Escalabilidad independiente de lectura y escritura<br>• Modificabilidad del esquema de consulta<br>• Disponibilidad de la consulta ante presión sobre el modelo transaccional<br><br>**Desfavorece:**<br>• Consistencia (pasa de fuerte a eventual)<br>• Simplicidad operativa (componente adicional con modos de falla propios)<br>• Testabilidad extremo a extremo<br>• Eficiencia de almacenamiento (datos duplicados) |
| **Arquitectura orientada a eventos (publicación/suscripción)** | **Favorece:**<br>• Desacople entre el proceso de evaluación y el modelo de lectura<br>• Escalabilidad del procesamiento asíncrono<br>• Integrabilidad con futuros consumidores (notificaciones, analítica)<br><br>**Desfavorece:**<br>• Consistencia inmediata<br>• Trazabilidad y depuración del flujo<br>• Complejidad de la infraestructura (broker, particiones, *consumer groups*) |
| **Microservicios (contexto general de Solventa)** | **Favorece:**<br>• Disponibilidad<br>• Escalabilidad<br>• Mantenibilidad<br>• Flexibilidad tecnológica<br><br>**Desfavorece:**<br>• Latencia extremo a extremo (saltos de red adicionales)<br>• Orquestación/coreografía<br>• Consistencia distribuida |

> La tensión que resuelve este experimento es visible en la tabla: el estilo de microservicios, ya adoptado en Solventa, **desfavorece la latencia**, y HA-08 es precisamente un ASR de latencia. CQRS se introduce como contramedida deliberada a esa contrapartida, no como preferencia estilística.

---

## 4. Tácticas de arquitectura asociadas al experimento

| Táctica de arquitectura asociada al experimento | Descripción |
|---|---|
| **Reducir la demanda computacional** | Para el sistema Solventa, el estado de un siniestro se compone hoy a partir de cinco entidades normalizadas (siniestro, póliza, hitos, documentos y peritaje), lo que obliga a la consulta a resolver *joins* y agregaciones en tiempo de petición. La táctica consiste en trasladar ese cómputo fuera del camino crítico: el proyector construye el estado completo una sola vez, en el momento en que ocurre el evento, y lo almacena listo para entregar. La consulta pasa a ser un acceso por clave primaria sin *joins* ni agregaciones. |
| **Mantener múltiples copias de los datos** | Se introducen dos copias derivadas del estado del siniestro: una proyección persistente en PostgreSQL, desnormalizada y con un registro por siniestro, y una copia volátil en Redis servida desde memoria. Cada copia acorta el camino de acceso a costa de introducir una ventana de desactualización que debe ser medida y acotada. |
| **Introducir concurrencia** | La actualización del modelo de lectura se ejecuta en un componente independiente (el proyector), que consume los eventos de dominio de forma asíncrona y trabaja en paralelo a las consultas de los clientes. El cliente nunca espera a que la proyección se actualice. |
| **Reducir el *overhead* de procesamiento** | El estado se almacena ya serializado (JSONB en la proyección, JSON en el caché) y se emplea un serializador de alto desempeño en la respuesta HTTP, de modo que la representación no se reconstruye en cada petición. |

---

## 5. Listado de componentes involucrados en el experimento

| Componente | Propósito y comportamiento esperado | Tecnología asociada |
|---|---|---|
| **API de Consulta de Siniestros** | Expone el recurso de consulta de estado de siniestro. Debe implementar los tres brazos del experimento sobre el mismo binario, seleccionables por configuración, de modo que la estrategia de lectura sea la única variable que cambie entre corridas. Devuelve una representación idéntica en los tres brazos. | Python, FastAPI, Uvicorn (uvloop), `asyncpg`, `redis-py`, `orjson` |
| **Proyector de Estado de Siniestro** | Consume los eventos de dominio del proceso de evaluación y actualiza la proyección materializada de forma idempotente. Debe descartar eventos con versión anterior a la almacenada e invalidar la entrada correspondiente del caché. Expone el *lag* de proyección como métrica. | Python, `aiokafka`, `asyncpg`, `redis-py`, `prometheus-client` |
| **Simulador del Proceso de Evaluación** | Genera cambios de estado sobre siniestros del conjunto caliente a una tasa configurable, escribiendo en el modelo transaccional y publicando el evento correspondiente. Mantiene la proyección bajo actualización activa durante toda la medición, condición exigida por el escenario EC-LAT-11. | Python, `aiokafka`, `asyncpg` |
| **Almacén Transaccional** | Contiene el modelo normalizado del proceso de evaluación. Es el origen de la verdad y la fuente de lectura del brazo A. Debe conservar sus índices para que la línea base sea una implementación razonablemente optimizada. | PostgreSQL 16, esquema `siniestros_w` |
| **Almacén de Proyección** | Contiene la vista materializada, un registro autocontenido por siniestro con la respuesta preconstruida. Es la fuente de lectura del brazo B y el respaldo del brazo C. | PostgreSQL 16, esquema `siniestros_r` |
| **Caché de Estado** | Almacena en memoria las entradas más consultadas bajo una política *cache-aside* con expiración e invalidación proactiva desde el proyector. | Redis 7 |
| **Plataforma de Observabilidad** | Recolecta la latencia interna del servicio, el *lag* de proyección, el *hit-rate* del caché y las métricas del generador de carga, para permitir la separación entre el costo del stack HTTP y el de la lógica de lectura. | Prometheus, Grafana, `prometheus-client` |

---

## 6. Listado de conectores involucrados en el experimento

| Conector | Comportamiento deseado en el experimento | Tecnología asociada |
|---|---|---|
| **Conector HTTP de consulta** | El generador de carga emite solicitudes contra el recurso de estado de siniestro a una **tasa de llegada fija** (no un número fijo de usuarios), de modo que la degradación del servicio no reduzca automáticamente la carga y enmascare el p95. Registra la latencia extremo a extremo por solicitud. | Cliente: k6 con ejecutor de tasa de llegada escalonada. Servidor: Uvicorn sobre ASGI. |
| **Conector de eventos asíncrono** | Cada cambio de estado del proceso de evaluación se publica como un evento particionado por identificador de siniestro, lo que garantiza el orden por agregado. Un consumidor perteneciente a un grupo dedicado procesa los eventos y actualiza la proyección. El evento transporta el estado completo (*event-carried state transfer*), de modo que el proyector nunca consulta de vuelta el modelo de escritura y el desacople exigido por HA-08 se preserva. | Publicador: `aiokafka` producer. Broker: Redpanda. Consumidor: `aiokafka` consumer con *consumer group*. |
| **Conector de acceso transaccional (brazo A)** | Resuelve la consulta componiendo el estado a partir de las cinco entidades normalizadas mediante *joins* y agregaciones en tiempo de petición. Representa la línea base contra la cual se mide la mejora. | `asyncpg` sobre PostgreSQL, esquema `siniestros_w`. Pool de conexiones de tamaño fijo. |
| **Conector de acceso a la proyección (brazos B y C)** | Resuelve la consulta mediante un acceso por clave primaria a un único registro, sin *joins* ni agregaciones. | `asyncpg` sobre PostgreSQL, esquema `siniestros_r`. |
| **Conector de caché (brazo C)** | Implementa *cache-aside*: ante un acierto devuelve la entrada en memoria; ante un fallo consulta la proyección, entrega el resultado y escribe la entrada con expiración. El proyector invalida la entrada al aplicar un cambio de estado, de modo que el caché nunca sirve una versión anterior a la ya proyectada. | `redis-py` en modo asíncrono sobre Redis 7, política `allkeys-lru`. |
| **Conector de telemetría** | La API y el proyector exponen métricas en formato de texto plano que Prometheus recolecta periódicamente; el generador de carga envía sus métricas por escritura remota al mismo Prometheus, de modo que latencia de cliente y de servidor queden en la misma línea de tiempo y sean comparables. | `prometheus-client` (exposición), Prometheus (*scrape* y *remote-write receiver*), Grafana (visualización). |

---

## 7. Tecnología asociada con el experimento

| Tecnología asociada con el experimento | Selección | Justificación |
|---|---|---|
| **Lenguajes de programación** | Python 3.12 | Alineado con el stack del equipo y con el resto de componentes de Solventa. Su modelo asíncrono permite representar fielmente el comportamiento de un servicio de lectura con E/S intensiva. |
| **Frameworks de desarrollo** | FastAPI + Uvicorn (uvloop, httptools) | Framework ASGI nativo asíncrono, necesario para que el camino de lectura no bloquee el *event loop*. Uvicorn con uvloop reduce el *overhead* del servidor, de modo que la latencia medida refleje la estrategia de lectura y no el transporte. |
| **Plataforma de despliegue** | Docker + Docker Compose V2 | Permite fijar límites explícitos de CPU y memoria por componente, condición indispensable para que las corridas sean reproducibles y comparables entre brazos en una estación de desarrollo. |
| **Bases de datos** | PostgreSQL 16 (esquemas `siniestros_w` y `siniestros_r`)<br>Redis 7 | PostgreSQL sostiene tanto el modelo normalizado como la proyección, lo que aísla la variable bajo estudio: la diferencia entre brazos A y B proviene del **modelo de datos**, no del motor. Redis aporta el almacenamiento en memoria del brazo C. |
| **Mensajería** | Redpanda | API compatible con Kafka, con un consumo de recursos considerablemente menor en un nodo único, lo que es determinante en un montaje local donde el broker compite por CPU con el generador de carga. |
| **Herramientas de análisis** | k6, Prometheus, Grafana | k6 ofrece un ejecutor de **tasa de llegada** (imprescindible para medir latencia correctamente) y umbrales declarativos que permiten codificar el criterio de aceptación del ASR en el propio script. Prometheus y Grafana correlacionan latencia de cliente, latencia interna, lag de proyección y consumo de recursos en una misma línea de tiempo. |
| **Librerías** | `asyncpg`, `redis-py` (asyncio), `aiokafka`, `orjson`, `pydantic`, `prometheus-client` | Drivers asíncronos en toda la ruta de lectura, requisito no negociable: un driver síncrono dentro de una corrutina bloquea el *event loop* completo y produciría una refutación falsa de la hipótesis. `orjson` minimiza el costo de serialización, que de otro modo contaminaría la comparación entre brazos. |

---

## 8. Distribución de actividades por integrante

| Integrante | Tareas a realizar | Esfuerzo estimado |
|---|---|---|
| **Alex Mauricio Rodriguez Sanchez** | **Desarrollar la API de Consulta de Siniestros:**<br>• Crear la aplicación FastAPI y el ciclo de vida de los *pools*.<br>• Implementar los tres brazos de lectura sobre el mismo binario.<br>• Instrumentar la latencia interna y el *hit-rate* del caché. | 15 horas |
| **Martin Ricardo Romero Ortiz** | **Preparar el entorno de ejecución:**<br>• Crear y configurar el `docker-compose.yml` con límites de recursos por componente.<br>• Configurar la red de Docker, PostgreSQL (parámetros de memoria), Redis y Redpanda.<br>• Configurar Prometheus, Grafana y el *remote-write* desde k6.<br>• Apoyar en la integración y ejecución de las corridas. | 15 horas |
| **Pedro Camilo Rojas Puertas** | **Desarrollar el Proyector y el Simulador:**<br>• Implementar el consumidor de eventos con *upsert* idempotente por versión.<br>• Implementar la invalidación del caché y la métrica de *lag*.<br>• Construir el simulador del proceso de evaluación sobre el conjunto caliente. | 15 horas |
| **Juan Camilo Acevedo Ospina** | **Planificar y dirigir el experimento:**<br>• Definir el contrato del evento de dominio y el modelo de la proyección.<br>• Generar el dataset sintético y verificar que el volumen supere la memoria del motor.<br>• Construir el script de carga y el protocolo de corridas contrabalanceadas.<br>• Analizar los resultados y redactar el informe final. | 15 horas |

**Total:** 60 horas — 1,5 semanas

> El esfuerzo debe recalibrarse una vez conocida la duración real de la generación del dataset, que es la actividad con mayor incertidumbre del cronograma.

---

## Anexo A — Diseño experimental

### Variables

| Tipo | Variable | Valores / control |
|---|---|---|
| **Independiente** | Estrategia de lectura | A (línea base) / B (proyección) / C (proyección + caché) |
| **Independiente** | TTL del caché | 0 s / 30 s / 300 s (sólo brazo C) |
| **Independiente** | Tasa de llegada | 10 / 25 / 50 / 80 solicitudes por segundo |
| **Dependiente** | Latencia extremo a extremo | p50, p95, p99 medidos en el generador de carga |
| **Dependiente** | Latencia interna del servicio | Histograma expuesto por la API |
| **Dependiente** | Tasa de error | Porcentaje de respuestas no exitosas |
| **Dependiente** | *Staleness* | Diferencia entre el instante del evento y el de su proyección |
| **Dependiente** | *Hit-rate* del caché | Sólo brazo C |
| **Controlada** | Volumen de datos | 1 000 000 de siniestros con sus entidades asociadas |
| **Controlada** | Recursos por componente | Límites explícitos de CPU y memoria |
| **Controlada** | Procesos de servidor | 2 *workers*, idéntico en los tres brazos |
| **Controlada** | Tamaño del *pool* de conexiones | Fijo e idéntico entre brazos |
| **Controlada** | Perfil de carga | Escalones idénticos y misma distribución de claves |
| **Controlada** | Representación de la respuesta | **JSON idéntico en los tres brazos** |
| **Controlada** | Carga de escritura concurrente | ~5 eventos por segundo durante toda la medición |

**Control crítico.** Si los tres brazos no devuelven exactamente la misma representación, parte de la diferencia medida provendría del tamaño de la respuesta y no de la arquitectura. El protocolo incluye una verificación automática de equivalencia antes de cada corrida.

**Factor adicional (brazo C').** En el brazo C el valor almacenado en el caché ya es una representación lista para entregar; omitir la revalidación y re-serialización acelera la respuesta, pero mezcla dos causas. Se mide por separado un brazo **C'** con esa omisión, de modo que la mejora atribuible al caché quede diferenciada de la atribuible a la serialización.

### Diseño de las corridas

Tres corridas independientes por brazo, con el orden de brazos contrabalanceado mediante un cuadrado latino:

| Corrida | Orden de ejecución |
|---|---|
| R1 | A → B → C |
| R2 | B → C → A |
| R3 | C → A → B |

El contrabalanceo neutraliza un sesgo que no se puede eliminar en un montaje local: el caché de páginas del sistema operativo no es limpiable de forma fiable dentro de Docker, por lo que un orden fijo haría que el primer brazo pagara sistemáticamente el costo del disco frío. Alternar el orden convierte ese sesgo sistemático en ruido aleatorio.

---

## Anexo B — Criterios de aceptación

**Se acepta la hipótesis HD-08 si**, en el escalón de operación regular y en **las tres corridas**:

- El p95 extremo a extremo del brazo C es **≤ 150 ms**
- La tasa de error es **< 1 %**
- El *lag* de proyección p95 es **≤ 2 s**
- Ninguna corrida queda invalidada por las verificaciones de sanidad definidas en la guía técnica

**Se refuta la hipótesis HD-08 si:**

- No se alcanza el umbral en el brazo C, **o**
- Se alcanza únicamente a costa de un *staleness* que haga que el cliente vea un estado desactualizado en el momento de mayor sensibilidad, lo cual contradice el propósito declarado de HA-08

**Resultado intermedio relevante.** Si el brazo B ya cumple el umbral, el caché constituye complejidad no justificada y la recomendación arquitectónica debe ser la alternativa más simple que satisface el ASR.

---

## Anexo C — Plantilla de registro de resultados

### Resultados por brazo (escalón de operación regular)

| Brazo | Corrida | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error (%) | Hit-rate (%) | Lag p95 (s) | ¿Cumple? |
|---|---|---|---|---|---|---|---|---|---|
| A | R1 | | | | | | n/a | n/a | |
| A | R2 | | | | | | n/a | n/a | |
| A | R3 | | | | | | n/a | n/a | |
| B | R1 | | | | | | n/a | | |
| B | R2 | | | | | | n/a | | |
| B | R3 | | | | | | n/a | | |
| C | R1 | | | | | | | | |
| C | R2 | | | | | | | | |
| C | R3 | | | | | | | | |
| C' | R1 | | | | | | | | |

### Consolidado y variabilidad

| Brazo | p95 medio (ms) | Desviación estándar | Mejora vs. A | Veredicto |
|---|---|---|---|---|
| A | | | — (referencia) | |
| B | | | | |
| C | | | | |
| C' | | | | |

> **Reportar la desviación estándar entre corridas es obligatorio.** Un p95 medio de 140 ms con desviación de 45 ms no es evidencia de cumplimiento del ASR: es evidencia de un sistema inestable que a veces cumple. La conclusión debe reflejarlo.

### Sensibilidad al TTL del caché (punto de sensibilidad 2)

| TTL | p95 (ms) | Hit-rate (%) | Staleness observado p95 (s) | ¿Aceptable para HA-08? |
|---|---|---|---|---|
| 0 s (sin caché) | | n/a | | |
| 30 s | | | | |
| 300 s | | | | |

### Sensibilidad a la carga (punto de sensibilidad 3)

| RPS | p95 brazo A | p95 brazo B | p95 brazo C |
|---|---|---|---|
| 10 | | | |
| 25 | | | |
| 50 | | | |
| 80 | | | |

Esta tabla identifica el punto de quiebre de cada alternativa, información arquitectónica más valiosa que un único número: indica cuánto margen de crecimiento ofrece cada decisión antes de incumplir el ASR.

---

## Anexo D — Amenazas a la validez

Esta sección debe aparecer íntegra en el informe final. Su omisión es el error más frecuente en experimentos de arquitectura, porque convierte una medición local en una afirmación sobre producción que la evidencia no respalda.

### Derivadas del montaje local

**El umbral absoluto de 150 ms no es transferible.** El hardware de desarrollo no es producción. Se reporta la **mejora relativa entre brazos** como resultado principal y el valor absoluto como indicativo, dejando explícito que la validación definitiva exige el ambiente productivo.

**Todo se ejecuta en un solo host, sin latencia de red entre componentes.** Esto *subestima* la latencia real, en la que API, base de datos y caché residen en nodos distintos. Mitigación opcional: inyectar 1–2 ms de latencia entre contenedores y reportar ambos escenarios.

**Contención de recursos.** El generador de carga, la plataforma de observabilidad, el broker y la base de datos compiten por la misma CPU. Mitigado con límites explícitos por componente y con la verificación de que el generador de carga no sea el cuello de botella.

**Caché de páginas del sistema operativo no controlable.** Mitigado mediante el contrabalanceo del orden de brazos descrito en el Anexo A.

### Derivadas del runtime

**Variabilidad en la cola de la distribución.** El intérprete introduce pausas por recolección de basura, y el *event loop* es cooperativo: una corrutina que no cede el control retrasa a las demás. Afecta sobre todo al p99 y en menor medida al p95. Mitigado con tres corridas independientes, descarte del período de calentamiento y reporte de la desviación entre corridas.

**Número de procesos de servidor como variable confusora.** Cada proceso utiliza un núcleo. Se fija en 2 e idéntico entre brazos, y el valor se declara en el informe.

**Asimetría de serialización.** Controlada mediante la separación de los brazos C y C'.

### Derivadas del diseño del experimento

**Representatividad del perfil de carga.** El modelo de conjunto caliente y frío (80 % de las consultas sobre el 20 % de los siniestros) es una aproximación razonada, no un dato medido en producción. Debe declararse como supuesto, señalando que el *hit-rate* del brazo C es sensible a él.

**Alcance de la simulación de eventos.** El simulador escribe y publica en dos pasos, sin patrón *transactional outbox*. No afecta la latencia de lectura medida, pero implica que el montaje no valida la consistencia extremo a extremo del flujo de escritura.

**Un solo tipo de consulta.** Se mide únicamente la consulta por identificador de siniestro. El escenario EC-LAT-11 menciona también la consulta de póliza, que este experimento no cubre.

---

## Anexo E — Siguientes iteraciones si se refuta la hipótesis

En orden de menor a mayor costo arquitectónico:

1. **Precarga del caché desde el proyector.** Sustituir la invalidación por escritura anticipada elimina el fallo en frío tras cada cambio de estado, a costa de escribir entradas que nadie consultará.
2. **Almacenamiento de la respuesta ya serializada.** Elimina toda serialización del camino crítico.
3. **Réplicas de lectura con balanceo.** Distribuye la carga de fallos de caché entre varias instancias.
4. **Particionado de la proyección** por rango de siniestro o por cliente, para reducir el tamaño de índice por partición.
5. **Revisión del contrato del recurso.** Si la representación completa es intrínsecamente pesada, dividirla en una consulta de estado liviana y una de historial bajo demanda. Esto modifica el diseño de la API, no sólo su implementación, y debe negociarse con los interesados.

---

## Anexo F — Trazabilidad

| Artefacto | Identificador |
|---|---|
| Historia de arquitectura | HA-08 |
| Escenario de calidad | EC-LAT-11 |
| Atributo de calidad | Latencia |
| Prioridad | (A,A) — ASR |
| Hipótesis de diseño | HD-08 (sub-hipótesis HD-08.1 a HD-08.4) |
| Tácticas | Reducir demanda computacional; mantener múltiples copias; introducir concurrencia; reducir *overhead* |
| Estilos | CQRS, orientado a eventos, microservicios |
| Vistas de arquitectura | Funcional (componentes), Información (datos), Despliegue (contenedores) |
| Proyecto Jira | SOLV |
| Documento técnico complementario | `Guia_Tecnica_HA-08.md` |
