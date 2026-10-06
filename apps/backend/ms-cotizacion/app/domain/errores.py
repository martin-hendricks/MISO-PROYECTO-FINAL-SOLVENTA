class ErrorDominio(Exception):
    codigo = "error_dominio"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo: str | None = None
        self.rango_valido: dict | None = None


class ReglaDeNegocioViolada(ErrorDominio):
    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.codigo = codigo


class NoEncontrado(ErrorDominio):
    codigo = "no_encontrado"


class ProductoInexistente(ReglaDeNegocioViolada):
    def __init__(self, producto: str) -> None:
        super().__init__("producto_inexistente", f"El producto '{producto}' no existe en el catálogo")
        self.campo = "producto"


class DatoRiesgoInvalido(ReglaDeNegocioViolada):
    """Dato del riesgo rechazado por el catálogo: nombra el campo y, si aplica, su rango válido."""

    def __init__(self, codigo: str, campo: str, mensaje: str, rango_valido: dict | None = None) -> None:
        super().__init__(codigo, mensaje)
        self.campo = campo
        self.rango_valido = rango_valido
