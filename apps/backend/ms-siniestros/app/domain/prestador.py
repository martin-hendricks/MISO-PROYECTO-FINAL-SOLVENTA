"""Catálogo de la red de atención. El tipo describe el local; los ramos, qué póliza lo cubre."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.errores import CoordenadaFueraDeRango, PrestadorSinRamo, RamoDesconocido, ReglaDeNegocioViolada

RAMOS_PRESTADOR = frozenset(
    {
        "proteccion-dispositivo",
        "soat-motocicleta",
        "microseguro-de-vida",
        "clima-y-vuelos",
        "vida-hipotecario",
        "pagos",
        "viaje",
        "vida-crediticia",
    }
)
TIPOS_PRESTADOR = frozenset(
    {
        "servicio-tecnico",
        "taller-motos",
        "ips-urgencias",
        "grua",
        "asistencia-viajero",
        "punto-aeropuerto",
        "ips-examenes",
        "funeraria",
        "centro-atencion",
    }
)
CIUDADES: dict[str, tuple[Decimal, Decimal]] = {
    "Bogotá": (Decimal("4.609700"), Decimal("-74.081700")),
    "Medellín": (Decimal("6.244200"), Decimal("-75.581200")),
    "Chía": (Decimal("4.861900"), Decimal("-74.059700")),
}
RADIO_MAX_KM = Decimal("50")
RADIO_DEFECTO_KM = Decimal("10")


def _exigir_ramos(ramos: frozenset[str]) -> None:
    if not ramos:
        raise PrestadorSinRamo()
    for ramo in ramos:
        if ramo not in RAMOS_PRESTADOR:
            raise RamoDesconocido(ramo)


def _exigir_coordenada(lat: Decimal, lng: Decimal) -> None:
    if not (Decimal("-90") <= lat <= Decimal("90") and Decimal("-180") <= lng <= Decimal("180")):
        raise CoordenadaFueraDeRango()


def _exigir_campos(nombre: str, tipo: str, direccion: str, ciudad: str, barrio: str, telefono: str, horario: str) -> None:
    if tipo not in TIPOS_PRESTADOR:
        raise ReglaDeNegocioViolada("tipo_desconocido", f"El tipo '{tipo}' no existe")
    if ciudad not in CIUDADES:
        raise ReglaDeNegocioViolada("ciudad_desconocida", f"La ciudad '{ciudad}' no existe")
    for campo, valor, tope in (
        ("nombre", nombre, 120),
        ("direccion", direccion, 200),
        ("barrio", barrio, 80),
        ("telefono", telefono, 40),
        ("horario", horario, 80),
    ):
        limpio = valor.strip()
        if not limpio or len(limpio) > tope:
            raise ReglaDeNegocioViolada("campo_invalido", f"Revisa el campo {campo}")


@dataclass(frozen=True)
class Centro:
    lat: Decimal
    lng: Decimal
    origen: str


@dataclass(frozen=True)
class Prestador:
    id: str
    nombre: str
    tipo: str
    direccion: str
    ciudad: str
    barrio: str
    lat: Decimal
    lng: Decimal
    telefono: str
    horario: str
    estado: str
    ramos: frozenset[str]
    creado_por: str
    creado_en: datetime
    actualizado_por: str
    actualizado_en: datetime

    @classmethod
    def crear(
        cls,
        *,
        nombre: str,
        tipo: str,
        ramos: frozenset[str],
        direccion: str,
        ciudad: str,
        barrio: str,
        lat: Decimal,
        lng: Decimal,
        telefono: str,
        horario: str,
        actor: str,
        ahora: datetime | None = None,
    ) -> Prestador:
        _exigir_ramos(ramos)
        _exigir_coordenada(lat, lng)
        _exigir_campos(nombre, tipo, direccion, ciudad, barrio, telefono, horario)
        momento = ahora or datetime.now(timezone.utc)
        return cls(
            id="PRE-" + secrets.token_hex(5).upper(),
            nombre=nombre.strip(),
            tipo=tipo,
            direccion=direccion.strip(),
            ciudad=ciudad,
            barrio=barrio.strip(),
            lat=lat,
            lng=lng,
            telefono=telefono.strip(),
            horario=horario.strip(),
            estado="activo",
            ramos=frozenset(ramos),
            creado_por=actor,
            creado_en=momento,
            actualizado_por=actor,
            actualizado_en=momento,
        )

    def editar(
        self,
        *,
        actor: str,
        ahora: datetime | None = None,
        nombre: str | None = None,
        tipo: str | None = None,
        ramos: frozenset[str] | None = None,
        direccion: str | None = None,
        ciudad: str | None = None,
        barrio: str | None = None,
        lat: Decimal | None = None,
        lng: Decimal | None = None,
        telefono: str | None = None,
        horario: str | None = None,
    ) -> Prestador:
        nuevo_lat = self.lat if lat is None else lat
        nuevo_lng = self.lng if lng is None else lng
        nuevos_ramos = self.ramos if ramos is None else ramos
        _exigir_ramos(nuevos_ramos)
        _exigir_coordenada(nuevo_lat, nuevo_lng)
        candidato = replace(
            self,
            nombre=(nombre if nombre is not None else self.nombre).strip(),
            tipo=tipo if tipo is not None else self.tipo,
            ramos=frozenset(nuevos_ramos),
            direccion=(direccion if direccion is not None else self.direccion).strip(),
            ciudad=ciudad if ciudad is not None else self.ciudad,
            barrio=(barrio if barrio is not None else self.barrio).strip(),
            lat=nuevo_lat,
            lng=nuevo_lng,
            telefono=(telefono if telefono is not None else self.telefono).strip(),
            horario=(horario if horario is not None else self.horario).strip(),
            actualizado_por=actor,
            actualizado_en=ahora or datetime.now(timezone.utc),
        )
        _exigir_campos(
            candidato.nombre,
            candidato.tipo,
            candidato.direccion,
            candidato.ciudad,
            candidato.barrio,
            candidato.telefono,
            candidato.horario,
        )
        return candidato

    def cambiar_estado(self, estado: str, actor: str, ahora: datetime | None = None) -> Prestador:
        if estado not in ("activo", "inactivo"):
            raise ReglaDeNegocioViolada("estado_desconocido", "El estado debe ser activo o inactivo")
        if estado == self.estado:
            return self
        return replace(self, estado=estado, actualizado_por=actor, actualizado_en=ahora or datetime.now(timezone.utc))


@dataclass(frozen=True)
class PrestadorCercano:
    prestador: Prestador
    distancia_km: float | None
