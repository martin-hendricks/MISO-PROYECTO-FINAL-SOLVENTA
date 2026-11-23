from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

router = APIRouter(prefix="/identidad", tags=["identidad"])

LIMITE_BYTES = 10 * 1024 * 1024


class VerificadorPruebaDeVida:
    """Stub: a non-empty JPEG of at most 10 MB is ok. Anything else is no. Raises when the stub is down."""

    def evaluar(self, contenido: bytes, tipo: str | None) -> str:
        es_jpeg = (tipo or "").split(";", 1)[0].strip().lower() == "image/jpeg"
        if contenido and es_jpeg and len(contenido) <= LIMITE_BYTES:
            return "ok"
        return "no"


def obtener_verificador() -> VerificadorPruebaDeVida:
    return VerificadorPruebaDeVida()


@router.post("/prueba-de-vida")
async def prueba_de_vida(
    foto: UploadFile = File(...),
    verificador: VerificadorPruebaDeVida = Depends(obtener_verificador),
) -> dict:
    contenido = await foto.read(LIMITE_BYTES + 1)
    try:
        resultado = verificador.evaluar(contenido, foto.content_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="servicio_no_disponible") from exc
    return {"resultado": resultado}
