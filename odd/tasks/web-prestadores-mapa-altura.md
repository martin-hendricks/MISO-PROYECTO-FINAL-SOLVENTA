# Prestadores (web): el mapa quedaba con 0 px de alto y la búsqueda por área volvía vacía

## Objetivo

Que la pantalla de prestadores con mapa de Google devuelva y muestre prestadores, y que un mapa sin tamaño nunca
dispare una búsqueda con un área vacía.

## Problema (reproducido el 2026-11-21 contra el sitio desplegado)

Un compañero llamó a `GET /v1/cliente/prestadores?norte=4.8619…&sur=4.8619…&este=-73.9967…&oeste=-74.1227…&lat=4.696…&lng=-74.112…&pais=CO`
y recibió **200 con la lista vacía**, cuando antes la pantalla traía prestadores. En la URL, `norte` y `sur` son
iguales: el rectángulo visible tiene altura cero.

El endpoint funciona y tiene datos (usuario de prueba, mismo punto):

| Parámetros | Respuesta |
| --- | --- |
| La URL exacta del compañero (`norte == sur`) | 200, **0 prestadores** |
| El mismo punto con un rectángulo válido alrededor de Bogotá | 200, 40 prestadores |
| Solo `lat`, `lng` y `pais` (radio de 10 km) | 200, 26 prestadores |

Con un navegador sin interfaz contra el sitio desplegado (ingreso con el usuario de prueba, pantalla
`/siniestros/prestadores`), en **todos** los tamaños de ventana probados (390, 820, 1024, 1366 y 1920 de ancho):

| Elemento | Medida |
| --- | --- |
| `.marco` (recuadro del mapa) | 420 px de alto |
| `google-map` y su contenedor interno | **0 px de alto** |
| Segunda petición a `/v1/cliente/prestadores` | `norte - sur = 0.000000` |
| Estado de la pantalla | `empty`, 0 filas: "No hay prestadores en esta zona." |

Causa: `google-map { height: 100% }` dentro de `.marco`, que solo tiene `min-height` y `flex: 1`, sin un alto
definido. El porcentaje no tiene contra qué resolverse y el mapa queda en 0 px. Sin superficie, `getBounds()`
devuelve `norte == sur`, el evento `idle` envía esa área como filtro y la búsqueda no encuentra nada.

### Por qué antes sí traía datos (coincide, no está demostrado)

El mapa solo existe si el despliegue inyecta la clave de Google Maps (`deploy-web.yml` la sustituye desde el
secreto `GOOGLE_MAPS_API_KEY`). Sin clave, la pantalla funciona en modo lista y pide por ubicación y radio, que sí
devuelve datos. El secreto se actualizó el 2026-11-21 a las 18:25 UTC y el primer despliegue del front posterior es
el de las 19:15 UTC. Los archivos del mapa no se han tocado desde el 2026-11-18. No se pudo inspeccionar qué traían
los builds anteriores.

## Cambios

| Archivo | Cambio |
| --- | --- |
| `mapa-prestadores.component.css` | `google-map { position: absolute; inset: 0; display: block }`: el mapa llena el marco con un alto definido. |
| `camara.ts` | `areaConSuperficie(area)`: `norte > sur` y `este > oeste`. |
| `prestadores-mapa.viewmodel.ts` | `alMoverCamara` ignora un área sin superficie en vez de buscarla. |

## Criterios de aceptación

- [x] Con la regla CSS exacta del cambio sustituida en el JavaScript desplegado (el mapa nace con ella, sin forzar
      ningún `resize`): mapa de 727×420 en escritorio y 358×420 en móvil, estado `ready`, y la petición lleva un área con
      superficie (`norte - sur = 0.0359`) con prestadores en la lista.
- [x] El test nuevo del view model falla sin la guarda (se lanza una consulta con el área vacía) y pasa con ella.
- [x] `pnpm test`: 682 en verde, cobertura al 100%. `pnpm build` sin errores.
- [ ] Tras el despliegue: la pantalla de prestadores muestra el mapa y trae prestadores.

## Limitaciones

- El componente `mapa-prestadores` también lo usa el back-office (lista y formulario de prestadores). El CSS se
  comparte, así que debería quedar corregido allí también, pero no se probó: requiere un usuario de operador.
- Los e2e del portal no ven este defecto: corren sin clave de Google Maps y, por tanto, sin mapa.
- El BFF responde 200 con una lista vacía ante un área sin superficie en vez de rechazarla. Se deja como está; la
  guarda del front evita llegar ahí, pero otro cliente que mande un área vacía recibiría el mismo resultado silencioso.
