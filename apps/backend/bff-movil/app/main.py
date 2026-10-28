import os

from fastapi import FastAPI

from .clients.bff_web import ClienteBffWeb
from .routers import cliente, registro, sesion

app = FastAPI(title="bff-movil")
app.state.bff_web = ClienteBffWeb(os.environ.get("BFF_WEB_BASE_URL"))
app.include_router(sesion.router)
app.include_router(registro.router)
app.include_router(cliente.router)
app.include_router(sesion.router, prefix="/v1")
app.include_router(registro.router, prefix="/v1")
app.include_router(cliente.router, prefix="/v1")
