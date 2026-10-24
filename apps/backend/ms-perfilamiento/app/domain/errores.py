class ErrorDominio(Exception):
    codigo = "error_dominio"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ReglaDeNegocioViolada(ErrorDominio):
    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.codigo = codigo


class TransicionInvalida(ErrorDominio):
    codigo = "transicion_invalida"

    def __init__(self, desde: str, hacia: str) -> None:
        super().__init__(f"No se puede pasar de '{desde}' a '{hacia}'")


class NoEncontrado(ErrorDominio):
    codigo = "no_encontrado"


class ConsentimientoNoOtorgado(ErrorDominio):
    """Precondición dura de HU-54: sin consentimiento de perfilamiento vigente no se
    invoca ningún adaptador de datos externos (Open Finance / Open Data). Se lanza
    ANTES de tocar cualquier adaptador, nunca después."""

    codigo = "consentimiento_no_otorgado"

    def __init__(self, cliente_id: str) -> None:
        super().__init__(f"El cliente {cliente_id} no tiene consentimiento de perfilamiento vigente")
