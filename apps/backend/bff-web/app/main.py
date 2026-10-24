from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import asesor, cliente, operador, registro, sesion

app = FastAPI(title="bff-web")

# El API Gateway (infra/terraform/modules/edge) ya agrega headers CORS a la
# respuesta, pero no responde el preflight por sí mismo: un OPTIONS que
# llega hasta aquí sin este middleware recibe 405 Method Not Allowed de
# FastAPI (solo hay handlers POST/GET registrados), y el navegador rechaza
# el preflight por no tener status 2xx aunque los headers CORS ya estén
# puestos (confirmado contra el API Gateway real). CORSMiddleware es quien
# debe responder el OPTIONS -- el navegador habla con este servicio, no con
# el API Gateway, en lo que a CORS respecta.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sesion.router)
app.include_router(registro.router)
app.include_router(cliente.router)
app.include_router(asesor.router)
app.include_router(operador.router)


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
