from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import jwt

ROLES = frozenset({"cliente", "asesor", "operador", "socio"})
ALGORITMO = "RS256"


class TokenInvalido(Exception):
    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


@dataclass(frozen=True)
class Identidad:
    sujeto: str
    rol: str
    alcances: frozenset[str] = frozenset()
    claims: Mapping[str, Any] = field(default_factory=dict, repr=False)


class ValidadorJWT:
    def __init__(
        self,
        llave_publica: str,
        emisor: str,
        audiencia: str,
        margen_segundos: int = 30,
    ) -> None:
        if not llave_publica.strip():
            raise ValueError("llave_publica vacía")
        self._llave = llave_publica
        self._emisor = emisor
        self._audiencia = audiencia
        self._margen = margen_segundos

    def validar(self, token: str) -> Identidad:
        try:
            claims = jwt.decode(
                token,
                self._llave,
                algorithms=[ALGORITMO],
                issuer=self._emisor,
                audience=self._audiencia,
                leeway=self._margen,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenInvalido("expirado") from exc
        except jwt.InvalidSignatureError as exc:
            raise TokenInvalido("firma_invalida") from exc
        except jwt.PyJWTError as exc:
            raise TokenInvalido("token_invalido") from exc

        if claims.get("typ") != "access":
            raise TokenInvalido("tipo_no_access")

        rol = claims.get("rol")
        if rol not in ROLES:
            raise TokenInvalido("rol_desconocido")

        alcances = claims.get("scope", "")
        return Identidad(
            sujeto=str(claims["sub"]),
            rol=rol,
            alcances=frozenset(alcances.split()) if isinstance(alcances, str) else frozenset(),
            claims=claims,
        )
