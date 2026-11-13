from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from .clients.nucleo import ClienteNucleo, RechazoNucleo, correlacion_saliente, token_saliente
from .observabilidad import instrumentar
from .routers import cliente, identidad, registro, sesion

app = FastAPI(title="bff-movil")
instrumentar(app)


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

@app.exception_handler(RechazoNucleo)
async def rechazo_nucleo(_: Request, exc: RechazoNucleo):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "codigo": exc.codigo})


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


# Swagger propio bajo /bff-movil/v1: el ALB no recorta el prefijo (mismo
# motivo que las rutas de negocio arriba), así que /docs y /openapi.json de
# FastAPI (montados en la raíz) nunca son alcanzables vía el API Gateway. No
# se usa `root_path` global porque afectaría las otras dos variantes de
# rutas ya montadas (sin prefijo, /v1) con el mismo prefijo /bff-movil/v1 en
# su schema. En su lugar, se genera el OpenAPI de la app real y se le
# reescribe `servers` al prefijo correcto, sin tocar las rutas existentes.
@app.get("/bff-movil/v1/openapi.json", include_in_schema=False)
def openapi_bff_movil() -> dict:
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema["servers"] = [{"url": "/bff-movil/v1"}]
    return schema


@app.get("/bff-movil/v1/docs", include_in_schema=False)
def docs_bff_movil():
    return get_swagger_ui_html(
        openapi_url="/bff-movil/v1/openapi.json",
        title=f"{app.title} - docs",
    )
