from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.ports.evidencias import ErrorAlmacenEvidencias


class AlmacenEvidenciasS3:
    """Adaptador S3 del puerto AlmacenEvidencias. En EKS toma credenciales por IRSA (sin
    llaves estáticas); en local apunta a LocalStack (S3) con S3_ENDPOINT_URL. boto3 es síncrono: cada
    llamada corre en un hilo para no bloquear el event loop."""

    def __init__(
        self,
        bucket: str,
        region: str,
        endpoint_url: str | None = None,
        endpoint_publico: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        kms_key_id: str | None = None,
    ) -> None:
        import boto3
        from botocore.config import Config

        self._bucket = bucket
        self._kms_key_id = kms_key_id
        config = Config(signature_version="s3v4", s3={"addressing_style": "path"}, retries={"max_attempts": 3})
        credenciales = (
            {"aws_access_key_id": access_key, "aws_secret_access_key": secret_key} if access_key else {}
        )
        self._cliente = boto3.client(
            "s3", region_name=region, endpoint_url=endpoint_url, config=config, **credenciales
        )
        # En local, el navegador no resuelve el host interno de Docker (s3:4566): las
        # URLs firmadas se generan contra el endpoint público (localhost:4566).
        self._cliente_firma = (
            boto3.client(
                "s3", region_name=region, endpoint_url=endpoint_publico, config=config, **credenciales
            )
            if endpoint_publico
            else self._cliente
        )

    @property
    def bucket(self) -> str:
        return self._bucket

    async def guardar(self, clave: str, contenido: bytes, content_type: str) -> None:
        extra = {"ContentType": content_type}
        if self._kms_key_id:
            extra |= {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": self._kms_key_id}
        try:
            await asyncio.to_thread(
                self._cliente.put_object, Bucket=self._bucket, Key=clave, Body=contenido, **extra
            )
        except Exception as exc:  # botocore lanza varias jerarquías; todas son falla del almacén
            raise ErrorAlmacenEvidencias(f"No se pudo guardar la evidencia: {type(exc).__name__}") from exc

    async def url_lectura(self, clave: str, expira_segundos: int = 300) -> str:
        # Firmar es un cálculo local (no hay llamada de red).
        return self._cliente_firma.generate_presigned_url(
            "get_object", Params={"Bucket": self._bucket, "Key": clave}, ExpiresIn=expira_segundos
        )

    async def asegurar_bucket(self) -> None:
        """Solo para local (LocalStack): en AWS el bucket lo crea Terraform (módulo s3_evidencias)."""

        def _crear() -> None:
            existentes = {b["Name"] for b in self._cliente.list_buckets().get("Buckets", [])}
            if self._bucket not in existentes:
                self._cliente.create_bucket(Bucket=self._bucket)

        await asyncio.to_thread(_crear)


@dataclass
class AlmacenEvidenciasEnMemoria:
    """Doble del puerto para pruebas y para correr el servicio sin S3 configurado."""

    bucket: str = "evidencias-en-memoria"
    objetos: dict[str, tuple[bytes, str]] = field(default_factory=dict)
    fallar: bool = False

    async def guardar(self, clave: str, contenido: bytes, content_type: str) -> None:
        if self.fallar:
            raise ErrorAlmacenEvidencias("Almacén de evidencias no disponible (simulado)")
        self.objetos[clave] = (contenido, content_type)

    async def url_lectura(self, clave: str, expira_segundos: int = 300) -> str:
        return f"memoria://{self.bucket}/{clave}?expira={expira_segundos}"
