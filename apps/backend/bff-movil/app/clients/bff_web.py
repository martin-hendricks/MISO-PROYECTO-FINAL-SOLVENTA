import httpx
from fastapi import HTTPException, Request

DETALLE_SIN_URL = "BFF_WEB_BASE_URL no configurado"
DETALLE_INCOMPLETA = "Respuesta de bff-web incompleta"


class ClienteBffWeb:
    def __init__(self, base_url: str | None) -> None:
        self._base = (base_url or "").strip().rstrip("/")

    def enviar(
        self,
        metodo: str,
        ruta: str,
        *,
        json: dict | None = None,
        autorizacion: str | None = None,
    ) -> dict:
        if not self._base:
            raise HTTPException(status_code=503, detail=DETALLE_SIN_URL)
        cabeceras = {"Authorization": autorizacion} if autorizacion else {}
        try:
            with httpx.Client(base_url=self._base, timeout=5.0) as http:
                respuesta = http.request(metodo, ruta, json=json, headers=cabeceras)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail="bff-web no disponible") from exc
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = {"detail": respuesta.text}
        if respuesta.status_code >= 400:
            detalle = cuerpo.get("detail", cuerpo) if isinstance(cuerpo, dict) else cuerpo
            raise HTTPException(status_code=respuesta.status_code, detail=detalle)
        if not isinstance(cuerpo, dict):
            raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
        return cuerpo


def es_v1(request: Request) -> bool:
    return request.url.path.startswith("/v1/")


def autorizacion(request: Request) -> str | None:
    return request.headers.get("authorization")


def proyectar(cuerpo: dict, claves: tuple[str, ...]) -> dict:
    if not isinstance(cuerpo, dict) or any(clave not in cuerpo for clave in claves):
        raise HTTPException(status_code=502, detail=DETALLE_INCOMPLETA)
    return {clave: cuerpo[clave] for clave in claves}
