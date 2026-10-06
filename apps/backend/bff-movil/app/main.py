from fastapi import FastAPI

from .routers import cliente, registro, sesion

app = FastAPI(title="bff-movil")
app.include_router(sesion.router)
app.include_router(registro.router)
app.include_router(cliente.router)
