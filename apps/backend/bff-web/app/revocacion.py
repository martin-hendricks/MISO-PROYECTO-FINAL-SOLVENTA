"""Blacklist de JTIs revocados (logout real de access/refresh tokens).

bff-web no tiene base de datos propia ni acceso a un store compartido como
Redis (confirmado: no hay ningún cliente redis/memcached configurado en este
servicio ni en bff-movil, ver app/config.py y app/main.py de ambos). Por eso
este store es un dict en memoria del propio proceso: {jti: exp_utc}.

LIMITACION IMPORTANTE A TENER EN CUENTA (no ocultar): infra/k8s/values/
bff-web.yaml tiene HPA habilitado con maxReplicas: 15 (hoy en 1 réplica solo
por el límite de memoria del ambiente mínimo/demo, ver el comentario de
`replicas` en ese archivo) -- en un despliegue real con más de una réplica,
una revocación hecha en la réplica A (por ejemplo, el logout de un usuario
atendido por el pod A) NO se propaga a la réplica B: un request posterior
que el load balancer enrute a B seguiría aceptando ese token hasta que
expire naturalmente (máximo 15 minutos). Es decir, el token queda revocado
de forma best-effort, no garantizada, cuando hay múltiples réplicas. Para
una propagación real entre réplicas se necesitaría un store compartido
(Redis/Memcached) que hoy no existe en este servicio; mitigar esto queda
fuera del alcance de esta iteración.

Las entradas se purgan de forma perezosa (en cada llamada) una vez que su
`exp` ya pasó, para no crecer sin límite -- los JWT de este servicio ya
expiran a los 15 minutos, así que la blacklist nunca retiene una entrada por
más tiempo que eso.
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
