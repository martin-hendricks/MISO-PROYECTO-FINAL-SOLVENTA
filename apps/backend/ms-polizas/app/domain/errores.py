class ErrorDominio(Exception):
    codigo = "error_dominio"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ReglaDeNegocioViolada(ErrorDominio):
    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.codigo = codigo


class NoEncontrado(ErrorDominio):
    codigo = "no_encontrado"


class TransicionInvalida(ErrorDominio):
    """Mismo patrón que ms-siniestros: una transición de estado (o una
    operación que exige un estado concreto) que el agregado no permite."""

    codigo = "transicion_invalida"

    def __init__(self, desde: str, hacia: str) -> None:
        super().__init__(f"No se puede pasar de '{desde}' a '{hacia}'")


class DependenciaNoDisponible(ErrorDominio):
    codigo = "dependencia_no_disponible"

    def __init__(self, servicio: str) -> None:
        super().__init__(f"No fue posible consultar {servicio}")
