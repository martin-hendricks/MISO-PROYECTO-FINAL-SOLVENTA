from fastapi import FastAPI

from .routers import asesor, cliente, operador, registro, sesion

app = FastAPI(title="bff-web")
app.include_router(sesion.router)
app.include_router(registro.router)
app.include_router(cliente.router)
app.include_router(asesor.router)
app.include_router(operador.router)


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
