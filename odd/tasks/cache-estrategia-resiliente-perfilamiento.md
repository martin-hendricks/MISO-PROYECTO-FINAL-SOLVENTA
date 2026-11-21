# Estrategia de caché de perfil: perfil vencido, presupuesto, circuit breaker y coalescencia

## Objetivo

Que `ms-perfilamiento` responda dentro de un tiempo acotado aunque Open Finance u Open Data
estén lentos o caídos, sin perder trazabilidad de qué dato se usó y sin retener datos de
quien revocó su consentimiento. Continúa `cache-redis-real-perfilamiento`, que dejó la
conexión a Redis funcionando.

## Problema (auditado el 2026-11-21 contra `develop` en `343650cb`)

| Dónde | Hallazgo |
| --- | --- |
| `AdaptadorConCache` | Si la caché no tiene el perfil espera al proveedor hasta el timeout del caso de uso. Con el proveedor lento, cada petición sin valor guardado paga esa espera completa. |
| TTL único (600 s) | Pasado el TTL el perfil desaparece de Redis y ya no sirve de respaldo, justo cuando el proveedor puede estar fallando. |
| Respaldo en memoria | El único respaldo ante un fallo es la memoria de cada proceso: se pierde al reiniciar y no se comparte entre réplicas. |
| Sin circuit breaker | Con el proveedor caído, cada petición lo invoca y espera su timeout. |
| Sin coalescencia | Varias peticiones concurrentes por la misma cédula disparan otras tantas invocaciones idénticas. |
| Trazabilidad | Un acierto de Redis se registraba como `modo=LIVE`: el snapshot no distinguía dato fresco de dato guardado. |
| Revocación | Solo invalida la memoria local. Redis conservaba el perfil hasta que venciera su TTL. |
| Observabilidad | Ninguna métrica de la caché, del proveedor ni del breaker. |

## Alcance

Dentro: `apps/backend/ms-perfilamiento/` (código, tests, README) y este plan. Solo aplica con
`REDIS_CACHE_OD_HOST` definido: sin Redis el comportamiento no cambia.

Fuera: alarmas de CloudWatch o Prometheus sobre las métricas nuevas, la decisión de cachear en
`ms-cotizacion`, y fijar con negocio qué proporción de respaldo es aceptable.

## Diseño

1. **Dos vigencias.** La suave (`REDIS_CACHE_OD_TTL_SECONDS`, 600 s) marca cuándo refrescar; la
   máxima (`REDIS_CACHE_OD_TTL_DURO_SECONDS`, 24 h) marca cuándo borrar. Lo vencido sigue
   sirviendo de respaldo.
2. **Presupuesto de respuesta** (`PRESUPUESTO_RESPUESTA_MS`, 120 ms). Si el proveedor no responde
   a tiempo se contesta con el perfil vencido, y la invocación sigue en segundo plano hasta
   `TIMEOUT_PROVEEDOR_MS` (700 ms) para repoblar la caché.
3. **Circuit breaker por tasa de fallo** sobre una ventana deslizante (10 s, umbral 50 %, mínimo de
   10 muestras). Abierto, no se invoca al proveedor; pasados 5 s deja pasar una sola sonda. Por
   tasa y no por fallos consecutivos, que abriría tarde con tráfico bajo.
4. **Coalescencia por clave:** las peticiones concurrentes comparten una invocación.
5. **Trazabilidad:** `modo=LIVE` si el dato vino del proveedor, `modo=CACHE` si salió de Redis, y
   `causa` (`timeout` o `fallo`) cuando se sirvió un valor vencido.
6. **Purga por consentimiento.** Como lo vencido se conserva hasta 24 h, revocar el consentimiento
   debe borrarlo de Redis. Cada entrada se anota en un conjunto por consentimiento, porque las
   entradas se indexan por cédula y quien revoca solo conoce el consentimiento. Si la purga falla no
   se revierte la revocación: se registra y la entrada vence sola.
7. **Métricas** `perfilamiento_*` con etiqueta `fuente`.

## Tareas

| ID | Tarea |
| --- | --- |
| T1 | `InterruptorCircuito` y `AdaptadorResiliente` (`app/infrastructure/resiliencia.py`), que reemplaza a `AdaptadorConCache`. |
| T2 | `CacheRedis` guarda atributos con su fecha de captura e indexa por consentimiento; puerto `CacheAtributos` y `PerfilGuardado`. |
| T3 | Caso de uso: usa el origen del dato para marcar `modo` y `causa`, y fija el consentimiento en curso. |
| T4 | `CacheFuentesConPurga`: la revocación también purga Redis. |
| T5 | Configuración, cableado en `main.py`, README y tests (unitarios e integración con Redis real). |

## Criterios de aceptación

- [x] Unitarias de `ms-perfilamiento` en verde (148); archivos nuevos y tocados al 100% en líneas y ramas.
- [x] Integración contra Redis real en verde (6): guardar y leer con fecha y TTL, perfil fresco sin
      llamar al proveedor, perfil vencido cuando el proveedor cae, purga por consentimiento, PING y
      rechazo sin token.
- [x] Servicio real en Docker (Postgres, Redis y la imagen) con Open Finance a 500 ms:
      sin valor guardado responde a los ~136 ms con el respaldo marcado `DEFAULT/timeout`;
      tras el refresco en segundo plano la siguiente petición sale de Redis en ~21 ms, `modo=CACHE`;
      con el proveedor caído y el perfil vencido responde a ~103 ms con `modo=CACHE`, `causa=fallo`;
      al revocar el consentimiento Redis queda sin claves y la oferta siguiente da 403.
- [x] Las métricas `perfilamiento_*` aparecen en `/metrics`.
- [ ] Desplegado en el clúster, con las métricas en Grafana.

## Limitaciones

- Con un proveedor lento y sin ningún valor guardado, la primera petición responde con el valor de
  respaldo aunque el proveedor habría contestado antes del timeout del caso de uso (400 ms). Es el
  costo de acotar la espera; la siguiente petición ya sale de la caché.
- El perfil vencido que se sirve no deja la edad del dato en el snapshot persistido, solo el modo y
  la causa. La edad queda en el log y no en la base.
- Qué proporción de respaldo es aceptable no está definida con negocio: sin ese número no hay
  alarma que configurar.
- El estado del breaker es por réplica, no compartido entre réplicas.
- El respaldo en memoria por proceso sigue existiendo como segunda capa, para cuando Redis no
  responde. No se retiró.
