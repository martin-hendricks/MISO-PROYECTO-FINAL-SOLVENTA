from fastapi import FastAPI

from .clients.nucleo import ClienteNucleo
from .routers import cliente, registro, sesion

app = FastAPI(title="bff-movil")
app.state.nucleo = ClienteNucleo()
app.include_router(sesion.router)
app.include_router(registro.router)
app.include_router(cliente.router)
app.include_router(sesion.router, prefix="/v1")
app.include_router(registro.router, prefix="/v1")
app.include_router(cliente.router, prefix="/v1")


@app.get("/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok"}
