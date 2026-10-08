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


class ProductoNoEncontrado(NoEncontrado):
    codigo = "producto_no_encontrado"

    def __init__(self, producto: str) -> None:
        super().__init__(f"Producto '{producto}' no existe en el catálogo")
        self.producto = producto
