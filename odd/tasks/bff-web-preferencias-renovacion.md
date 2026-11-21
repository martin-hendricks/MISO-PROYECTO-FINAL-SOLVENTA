# bff-web: guardar la renovación automática de una póliza responde 500

## Objetivo

Que `PATCH /v1/cliente/polizas/{numero}/preferencias` guarde la preferencia de renovación automática.

## Problema (observado el 2026-11-21 en el clúster, durante las pruebas de emisión)

Justo después de emitir una póliza, activar la renovación automática falla. Del log de `bff-web`:

| Hora (UTC) | Petición | Respuesta |
| --- | --- | --- |
| 18:55:47 | `POST /v1/cliente/polizas` | 200 (la emisión de punta a punta ya funcionaba) |
| 18:55:49 | `PATCH /v1/cliente/polizas/POL-2026-00000001/preferencias` | **500** |

`ms-polizas` no recibió ninguna consulta de esa petición (no hay `GET /v1/polizas/numero/...` entre las 18:55:47 y
las 18:55:52), así que la falla ocurre dentro de `bff-web`, antes de llamar al servicio.

Causa: `ContextoUsuario.usuario_id` ya es un `UUID` (`self.usuario_id = UUID(correo)`), y la ruta hacía
`UUID(contexto.usuario_id)`. `UUID()` sobre un `UUID` lanza `AttributeError: 'UUID' object has no attribute
'replace'`, que sale como 500. Las demás rutas pasan `contexto.usuario_id` directo. `obtener_por_numero` ya acepta un
`UUID` (hace `str()` por dentro), así que la conversión sobraba. No había ningún test de esta ruta.

`bff-movil` tiene la misma ruta pero maneja el id como texto: no tiene el defecto.

## Alcance

Dentro: `apps/backend/bff-web/app/routers/cliente.py` (`guardar_renovacion`) y un test nuevo.
Fuera: el resto de rutas, que ya pasan el id correctamente.

## Tareas

| ID | Tarea |
| --- | --- |
| T1 | Pasar `contexto.usuario_id` sin envolverlo en `UUID()`, y `str(contexto.usuario_id)` a `guardar_preferencia`, cuyo parámetro es texto. |
| T2 | Tests: la ruta guarda y reenvía el mismo `usuario_id` en las dos llamadas a `ms-polizas`, desactivar la renovación, y el rol cliente es obligatorio. |

## Criterios de aceptación

- [x] El test nuevo falla con el código anterior con el mismo `AttributeError` del clúster, y pasa con el arreglo.
- [x] Suite de `bff-web` en verde: 234 pasan, 2 se saltan.
- [ ] Tras el despliegue: activar y desactivar la renovación automática de una póliza recién emitida responde 200.

## Limitaciones

- El usuario reportó un 503 y el log muestra un 500 en `bff-web`. No se pudo conciliar: puede ser cómo lo muestra el
  front, o un intento distinto. Es el único 5xx de `bff-web` en el periodo revisado.
- Los e2e del portal web simulan el BFF en el navegador, así que no podían detectar este defecto: solo un test del
  propio `bff-web` o una prueba contra el clúster lo ven.
