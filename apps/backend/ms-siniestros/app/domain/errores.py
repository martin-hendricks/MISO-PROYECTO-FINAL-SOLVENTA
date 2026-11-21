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


class EventoParametricoInvalido(ReglaDeNegocioViolada):
    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(codigo, mensaje)


class PrestadorSinRamo(ReglaDeNegocioViolada):
    def __init__(self) -> None:
        super().__init__("prestador_sin_ramo", "Elige al menos un ramo.")


class RamoDesconocido(ReglaDeNegocioViolada):
    def __init__(self, ramo: str) -> None:
        super().__init__("ramo_desconocido", f"El ramo '{ramo}' no existe")


class CoordenadaFueraDeRango(ReglaDeNegocioViolada):
    def __init__(self) -> None:
        super().__init__("coordenada_fuera_de_rango", "La coordenada está fuera de rango")


class CentroRequerido(ReglaDeNegocioViolada):
    def __init__(self) -> None:
        super().__init__("centro_requerido", "Indica una ubicación o una ciudad")


class PaisDesconocido(ReglaDeNegocioViolada):
    def __init__(self, pais: str) -> None:
        super().__init__("pais_desconocido", f"El país '{pais}' no existe")


class CiudadDesconocida(ReglaDeNegocioViolada):
    def __init__(self, pais: str, ciudad: str) -> None:
        super().__init__("ciudad_desconocida", f"La ciudad '{ciudad}' no existe en {pais}")


class AreaInvalida(ReglaDeNegocioViolada):
    def __init__(self) -> None:
        super().__init__("area_invalida", "El área visible no es válida")
