from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .tokens import ALGORITMO

EMISOR_PRUEBAS = "ms-identidad"
AUDIENCIA_PRUEBAS = "solventa"


class EmisorDePrueba:
    def __init__(self, emisor: str = EMISOR_PRUEBAS, audiencia: str = AUDIENCIA_PRUEBAS) -> None:
        self._llave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.emisor = emisor
        self.audiencia = audiencia
        self.llave_publica_pem = (
            self._llave.public_key()
            .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
            .decode()
        )

    def emitir(
        self,
        sujeto: str = "USR-1",
        rol: str = "cliente",
        alcances: tuple[str, ...] = (),
        expira_en: int = 900,
        **extra: object,
    ) -> str:
        ahora = datetime.now(UTC)
        claims = {
            "sub": sujeto,
            "rol": rol,
            "typ": "access",
            "scope": " ".join(alcances),
            "iss": self.emisor,
            "aud": self.audiencia,
            "iat": ahora,
            "exp": ahora + timedelta(seconds=expira_en),
            **extra,
        }
        return jwt.encode(claims, self._llave, algorithm=ALGORITMO)
