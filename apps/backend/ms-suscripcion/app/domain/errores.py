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


class ReglaNoConfigurada(ErrorDominio):
    codigo = "regla_no_configurada"
