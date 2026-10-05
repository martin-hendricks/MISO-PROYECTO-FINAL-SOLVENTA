# solventa-seguridad

Librería interna que comparten `bff-web` y `bff-movil`. HU-76 pide que el control sea **compartido, no reimplementado**: un solo validador para los dos canales.

| Qué | HU | Dónde |
| --- | --- | --- |
| Validar firma, expiración, emisor, audiencia y tipo del JWT en cada petición | HU-74 / HU-76 | `tokens.ValidadorJWT` |
| Denegar en servidor las acciones fuera del rol (`cliente`, `asesor`, `operador`, `socio`) | HU-75 | `requiere_rol(...)` |
| Denegar por alcance (`scope`) | HU-74 | `requiere_alcance(...)` |
| Auditar cada rechazo (usuario, rol, acción, motivo, hora) **sin escribir el token** | HU-74 / HU-75 | `auditoria.registrar_rechazo` |

## Decisiones

- **RS256, solo validación.** `ms-identidad` firma con su llave privada y los BFF solo tienen la llave pública, así que un BFF no puede fabricar tokens. El algoritmo está fijado: un token HS256 se rechaza aunque esté "firmado" con la llave pública.
- **401 sin detalles.** Un token expirado, mal firmado o ausente responde `{"detail": "No autorizado"}`. El motivo real solo va al log de auditoría.
- **Falla cerrada.** Si el BFF arranca sin llave pública, las rutas protegidas responden 503 y nunca quedan abiertas.
- Claims esperados: `sub`, `rol`, `typ=access`, `scope` (alcances separados por espacio), `iss`, `aud`, `iat` y `exp`. Este es el contrato que debe cumplir `ms-identidad` al emitir.

## Uso

```python
from fastapi import APIRouter, Depends
from solventa_seguridad import ValidadorJWT, configurar_seguridad, identidad_actual, requiere_rol

configurar_seguridad(app, ValidadorJWT(llave_publica_pem, emisor="ms-identidad", audiencia="solventa"))

v1 = APIRouter(prefix="/v1", dependencies=[Depends(identidad_actual)])   # todo /v1 protegido

@v1.post("/avisos/decision", dependencies=[Depends(requiere_rol("operador"))])
async def decidir(...): ...
```

Para tests, `solventa_seguridad.pruebas.EmisorDePrueba` genera un par de llaves efímero y firma tokens. **Solo para tests**: en producción el único emisor es `ms-identidad`.

## Desarrollo

```bash
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[test]"
pytest --cov
```

Los BFF la instalan sola: su `pyproject.toml` la declara con una ruta relativa (`{root:parent:uri}/libs/solventa-seguridad`).
