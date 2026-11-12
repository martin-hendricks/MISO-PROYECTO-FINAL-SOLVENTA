from fastapi import FastAPI, Request

from .clients.nucleo import ClienteNucleo, correlacion_saliente, token_saliente
from .routers import cliente, identidad, registro, sesion

app = FastAPI(title="bff-movil")


@app.middleware("http")
async def reenviar_token(request: Request, call_next):
    autorizacion = request.headers.get("authorization", "")
    token = autorizacion.removeprefix("Bearer ").strip() if autorizacion.lower().startswith("bearer ") else None
    marca = token_saliente.set(token)
    marca_correlacion = correlacion_saliente.set(request.headers.get("x-correlation-id"))
    try:
        return await call_next(request)
    finally:
        token_saliente.reset(marca)
        correlacion_saliente.reset(marca_correlacion)

app.state.nucleo = ClienteNucleo()
app.include_router(sesion.router)
app.include_router(registro.router)
app.include_router(cliente.router)
app.include_router(sesion.router, prefix="/v1")
app.include_router(registro.router, prefix="/v1")
app.include_router(cliente.router, prefix="/v1")
app.include_router(identidad.router, prefix="/v1")
# /bff-movil/v1/*: bff-web y bff-movil comparten los mismos paths /v1/* (ver
# sesion/registro/cliente), y el ALB de infra/terraform/environments/minimo
# solo distingue por path prefix (nunca por host/header) -- sin un prefijo
# propio, la regla de bff-web siempre gana y bff-movil queda inalcanzable.
# El ALB no recorta el prefijo antes de reenviar (acción "forward" simple),
# así que el pod necesita responder al path completo, con el prefijo
# incluido. La app Android apunta su base URL a .../bff-movil en vez de
# cambiar nada más del contrato.
app.include_router(sesion.router, prefix="/bff-movil/v1")
app.include_router(registro.router, prefix="/bff-movil/v1")
app.include_router(cliente.router, prefix="/bff-movil/v1")
app.include_router(identidad.router, prefix="/bff-movil/v1")


@app.get("/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok"}
