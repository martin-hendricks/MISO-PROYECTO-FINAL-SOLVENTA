""":AdaptadorTelemetria — un adaptador por proveedor (capa anticorrupción).

Cada adaptador valida el esquema propio de su proveedor y lo traduce al
EventoTelemetria canónico. Sumar un proveedor es agregar un módulo y registrarlo
aquí: ni la ruta ni el consumidor cambian (EC-MOD-05, EC-INT-03).
"""

from typing import Protocol

from app.domain.evento import EventoTelemetria

from .clima import AdaptadorClima
from .vuelos import AdaptadorVuelos


class AdaptadorTelemetria(Protocol):
    proveedor: str

    def traducir(self, carga: dict) -> EventoTelemetria: ...


ADAPTADORES: dict[str, AdaptadorTelemetria] = {
    a.proveedor: a for a in (AdaptadorVuelos(), AdaptadorClima())
}
