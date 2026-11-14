"""Blacklist de JTIs revocados (logout real de access/refresh tokens).

Mismo mecanismo que apps/backend/bff-web/app/revocacion.py -- ver ese
archivo para el detalle completo del diseño y su limitación. Se duplica en
vez de compartirse porque bff-web y bff-movil son procesos independientes,
cada uno con su propio ciclo de deploy (ver apps/backend/docker-compose.yml:
"bff-movil y bff-web son pares... ninguno llama al otro"), así que no hay
forma de compartir este estado en memoria entre ambos sin un store externo
que hoy no existe en ninguno de los dos.

LIMITACION IMPORTANTE A TENER EN CUENTA (no ocultar): infra/k8s/values/
bff-movil.yaml tiene HPA habilitado con maxReplicas: 10 (hoy en 1 réplica
solo por el ambiente mínimo/demo) -- con más de una réplica en un
despliegue real, una revocación en la réplica A no se propaga a la réplica
B hasta que el token expire naturalmente (máximo 15 minutos). Mitigar esto
requeriría un store compartido (Redis/Memcached) que no existe hoy en este
servicio.
"""

from datetime import datetime, timezone
from threading import Lock

_revocados: dict[str, datetime] = {}
_lock = Lock()


def _purgar_expirados(ahora: datetime) -> None:
    expirados = [jti for jti, exp in _revocados.items() if exp <= ahora]
    for jti in expirados:
        del _revocados[jti]


def revocar(jti: str, exp: datetime) -> None:
    """Marca `jti` como revocado hasta su expiración `exp` (UTC)."""
    if not jti:
        return
    ahora = datetime.now(timezone.utc)
    with _lock:
        _purgar_expirados(ahora)
        _revocados[jti] = exp


def esta_revocado(jti: str) -> bool:
    if not jti:
        return False
    ahora = datetime.now(timezone.utc)
    with _lock:
        _purgar_expirados(ahora)
        return jti in _revocados
