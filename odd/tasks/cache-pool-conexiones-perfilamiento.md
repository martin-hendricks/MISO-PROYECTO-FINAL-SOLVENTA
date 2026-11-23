# Caché Redis: contexto SSL compartido y pool calentado

## Objetivo

Que la caché Redis de `ms-perfilamiento` no pierda operaciones ni bloquee el servicio por el costo de
abrir conexiones nuevas a ElastiCache, ni deje sin perfil vencido de respaldo a una petición justo
cuando el proveedor falla.

## Problema (medido el 2026-11-21 en el clúster, tras desplegar #225 y #228)

Desde el pod de `ms-perfilamiento` contra ElastiCache (TLS + token):

| Medida | Resultado |
| --- | --- |
| Conexión nueva con `redis-py`, 25 muestras | mín 63,8 · p50 79,9 · p95 122,3 · máx 127,6 ms |
| `GET` con la conexión ya abierta, 200 muestras | p50 0,72 · p95 3,29 · máx 7,60 ms |
| Desglose de una conexión nueva a mano: DNS + TCP + TLS + autenticación | 0,6 + 0,5 + 3,7 + 1,0 = **~6 ms** |
| `ssl.create_default_context()` | p50 69,7 · máx 90,6 ms |
| Conexión nueva reutilizando un único contexto SSL | p50 **7,8** · máx 31,5 ms |
| Retraso del event loop mientras se abrían 8 conexiones | hasta 79 ms |

**La causa no es la red, ni ElastiCache, ni el tamaño del nodo, ni CPU estrangulada** (el pod corre en
un t3.small con límite de 500m y no se estranguló). `redis-py` construye un contexto SSL nuevo por cada
conexión y eso cuesta unos 70 ms de CPU, síncronos dentro del event loop. `TIMEOUT_CACHE_MS` es 50 ms,
así que:

- Toda operación que necesita una conexión nueva expira y se salta la caché (los dos avisos del log y
  los dos errores de `perfilamiento_cache_errores_total` coinciden con la primera petición de la prueba).
- Si el proveedor falla en ese momento, la lectura del perfil vencido también expira y el respaldo no
  está disponible.
- Mientras se construye el contexto, el servicio entero deja de atender peticiones unos 70 ms.

Más CPU lo reduciría pero no lo quita, y no lo medí con otros recursos.

## Alcance

Dentro: `apps/backend/ms-perfilamiento/` (configuración, `main.py`, `infrastructure/cache.py`,
tests, README) y este plan.

Fuera: subir `TIMEOUT_CACHE_MS` (cada petición con la caché caída pagaría más antes del presupuesto
de respuesta), y el estado del breaker compartido entre réplicas.

## Diseño

1. **Contexto SSL compartido** (`crear_cliente_redis`): las conexiones TLS de un pool comparten el
   primer contexto que se construya, y cada pool tiene el suyo. Es la causa raíz: una conexión nueva
   baja de ~79 a ~8 ms y deja de bloquear el event loop.
2. **Calentar el pool al arrancar** (`REDIS_CACHE_OD_POOL_CALENTAMIENTO`, 8): se toman N conexiones del
   pool y se devuelven, de modo que quedan abiertas. Se hizo así y no con PING en paralelo porque,
   medido contra Redis real, los PING rápidos terminan y liberan su conexión para los siguientes:
   pidiendo 5, 8 y 20 se abrieron 3, 4 y 6. Tomando las conexiones del pool se abren exactamente 5, 8 y 20.
3. **Mantenerlas vivas:** `socket_keepalive` y `health_check_interval` (30 s).
4. **Acotar el pool** (`REDIS_CACHE_OD_POOL_MAX`, 32 por réplica).
5. Los 50 ms se quedan para los comandos. Si el PING inicial falla no se intenta calentar.
6. Al apagar se cierra el pool (`aclose(close_connection_pool=True)`): el cliente no cierra un pool que le pasan.

## Tareas

| ID | Tarea |
| --- | --- |
| T1 | `crear_cliente_redis` con contexto SSL compartido por pool, pool acotado, keepalive y verificación. |
| T2 | `calentar_conexiones` y su llamada al arrancar. |
| T3 | Configuración (`pool_calentamiento`, `pool_max`, `health_check_s`) y cableado en `main.py`. |
| T4 | Tests unitarios y de integración contra Redis real, también con TLS local; README. |

## Criterios de aceptación

- [x] Unitarias de `ms-perfilamiento` en verde (157); archivos tocados al 100% en líneas y ramas.
- [x] Integración contra Redis real en verde (9): tras calentar el servidor ve exactamente las
      conexiones pedidas y una ráfaga no abre ninguna nueva; con TLS local el pool crea el contexto SSL
      **una vez** (el cliente por defecto crea 5 para 5 conexiones, test de control).
- [x] Imagen real arrancada contra Redis: `8 conexiones abiertas al arrancar`; el servidor ve 8 del
      servicio y al apagarlo se cierran.
- [ ] En el clúster, tras desplegar: conexión nueva por debajo de 50 ms (era 64–128 ms) y la primera
      petición sin avisos `no disponible` ni errores nuevos en `perfilamiento_cache_errores_total`.

## Limitaciones

- No se probó el certificado de Amazon ni el token de ElastiCache en local; eso se valida al desplegar.
- Una ráfaga por encima de las conexiones calentadas sigue abriendo conexiones nuevas; ahora cuestan
  ~8 ms y no bloquean el loop, pero no están garantizadas por debajo de 50 ms.
- Si Redis cambia de nodo (failover), las conexiones se rehacen y esas operaciones pagan el costo de abrirlas.
- La mejora por tamaño de infraestructura no se midió.
