from uuid import uuid4

import pytest

from app.application import casos_uso_clientes
from app.domain.errores import NoEncontrado
from app.domain.modelos import EstadoUsuario, Usuario


class _ConsultaConsentimientoDoble:
    """Doble de ConsultaConsentimiento (ms-consentimiento)."""

    def __init__(self, vigente: bool = False) -> None:
        self._vigente = vigente
        self.consultados: list[str] = []

    async def vigente(self, cliente_id: str) -> bool:
        self.consultados.append(cliente_id)
        return self._vigente


class _ConsultaPerfilamientoDoble:
    """Doble de ConsultaPerfilamiento (ms-perfilamiento)."""

    def __init__(self, pendiente: bool = False) -> None:
        self._pendiente = pendiente
        self.consultados: list[str] = []

    async def tiene_originacion_pendiente(self, cliente_id: str) -> bool:
        self.consultados.append(cliente_id)
        return self._pendiente


def _cliente(**overrides) -> Usuario:
    usuario = Usuario.crear(
        tipo_documento="CC",
        numero_documento=overrides.pop("numero_documento", "1012345678"),
        email=overrides.pop("email", "camila@correo.com"),
        password_plano="clave-secreta-123",
        canal=overrides.pop("canal", "web"),
    )
    for clave, valor in overrides.items():
        setattr(usuario, clave, valor)
    return usuario


async def _agregar(almacen, usuario: Usuario) -> Usuario:
    almacen.usuarios[usuario.id] = usuario
    return usuario


# --- resolver_consentimiento ------------------------------------------------


async def test_resolver_consentimiento_con_originacion_abierta_es_hipotecario_pendiente():
    resultado = await casos_uso_clientes.resolver_consentimiento(
        uuid4(),
        _ConsultaConsentimientoDoble(vigente=True),
        _ConsultaPerfilamientoDoble(pendiente=True),
    )

    assert resultado == casos_uso_clientes.HIPOTECARIO_PENDIENTE


async def test_resolver_consentimiento_sin_originacion_y_con_habeas_data_vigente():
    resultado = await casos_uso_clientes.resolver_consentimiento(
        uuid4(),
        _ConsultaConsentimientoDoble(vigente=True),
        _ConsultaPerfilamientoDoble(pendiente=False),
    )

    assert resultado == casos_uso_clientes.HABEAS_DATA


async def test_resolver_consentimiento_sin_nada_es_revocado():
    resultado = await casos_uso_clientes.resolver_consentimiento(
        uuid4(),
        _ConsultaConsentimientoDoble(vigente=False),
        _ConsultaPerfilamientoDoble(pendiente=False),
    )

    assert resultado == casos_uso_clientes.REVOCADO


async def test_resolver_consentimiento_prioriza_originacion_sobre_habeas_data_revocado():
    """Aunque no haya habeas data vigente, una originación abierta manda."""
    resultado = await casos_uso_clientes.resolver_consentimiento(
        uuid4(),
        _ConsultaConsentimientoDoble(vigente=False),
        _ConsultaPerfilamientoDoble(pendiente=True),
    )

    assert resultado == casos_uso_clientes.HIPOTECARIO_PENDIENTE


# --- listar_clientes ---------------------------------------------------------


async def test_listar_clientes_devuelve_solo_rol_cliente_con_consentimiento_resuelto(uow, almacen):
    cliente = await _agregar(almacen, _cliente(email="cliente@correo.com", numero_documento="1"))
    asesor = await _agregar(almacen, _cliente(email="asesor@solventa.com", numero_documento="2", rol="asesor"))

    pares = await casos_uso_clientes.listar_clientes(
        uow, _ConsultaConsentimientoDoble(vigente=True), _ConsultaPerfilamientoDoble(pendiente=False)
    )

    ids = {usuario.id for usuario, _ in pares}
    assert cliente.id in ids
    assert asesor.id not in ids
    assert all(valor == casos_uso_clientes.HABEAS_DATA for _, valor in pares)


async def test_listar_clientes_vacio_cuando_no_hay_clientes(uow):
    pares = await casos_uso_clientes.listar_clientes(
        uow, _ConsultaConsentimientoDoble(), _ConsultaPerfilamientoDoble()
    )

    assert pares == []


# --- obtener_cliente ----------------------------------------------------------


async def test_obtener_cliente_devuelve_la_ficha_y_el_consentimiento(uow, almacen):
    cliente = await _agregar(almacen, _cliente())

    usuario, valor = await casos_uso_clientes.obtener_cliente(
        uow, cliente.id, _ConsultaConsentimientoDoble(vigente=True), _ConsultaPerfilamientoDoble(pendiente=False)
    )

    assert usuario.id == cliente.id
    assert valor == casos_uso_clientes.HABEAS_DATA


async def test_obtener_cliente_inexistente_es_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso_clientes.obtener_cliente(
            uow, uuid4(), _ConsultaConsentimientoDoble(), _ConsultaPerfilamientoDoble()
        )


async def test_obtener_cliente_con_rol_distinto_es_no_encontrado(uow, almacen):
    asesor = await _agregar(almacen, _cliente(rol="asesor"))

    with pytest.raises(NoEncontrado):
        await casos_uso_clientes.obtener_cliente(
            uow, asesor.id, _ConsultaConsentimientoDoble(), _ConsultaPerfilamientoDoble()
        )


# --- actualizar_estado_cliente ------------------------------------------------


async def test_actualizar_estado_cliente_desactiva(uow, almacen):
    cliente = await _agregar(almacen, _cliente())

    actualizado = await casos_uso_clientes.actualizar_estado_cliente(uow, cliente.id, EstadoUsuario.INACTIVO)

    assert actualizado.estado is EstadoUsuario.INACTIVO
    assert almacen.usuarios[cliente.id].estado is EstadoUsuario.INACTIVO


async def test_actualizar_estado_cliente_reactiva(uow, almacen):
    cliente = await _agregar(almacen, _cliente(estado=EstadoUsuario.INACTIVO))

    actualizado = await casos_uso_clientes.actualizar_estado_cliente(uow, cliente.id, EstadoUsuario.ACTIVO)

    assert actualizado.estado is EstadoUsuario.ACTIVO


async def test_actualizar_estado_cliente_inexistente_es_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso_clientes.actualizar_estado_cliente(uow, uuid4(), EstadoUsuario.INACTIVO)


async def test_actualizar_estado_cliente_con_rol_distinto_es_no_encontrado(uow, almacen):
    asesor = await _agregar(almacen, _cliente(rol="asesor"))

    with pytest.raises(NoEncontrado):
        await casos_uso_clientes.actualizar_estado_cliente(uow, asesor.id, EstadoUsuario.INACTIVO)
