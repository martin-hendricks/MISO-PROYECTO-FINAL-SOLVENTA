class ErrorDominio(Exception):
    codigo = "error_dominio"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class CuentaDuplicada(ErrorDominio):
    """Correo o documento ya registrados. Nunca se expone cuál de los dos
    chocó: evita que alguien use el alta para confirmar si un correo ya
    existe en el sistema."""

    codigo = "cuenta_duplicada"

    def __init__(self, mensaje: str = "La cuenta ya existe") -> None:
        super().__init__(mensaje)


class CredencialesInvalidas(ErrorDominio):
    """Correo inexistente o contraseña incorrecta. Un solo error para ambos
    casos: no se revela cuál de las dos cosas falló (evita enumeración de
    cuentas)."""

    codigo = "credenciales_invalidas"

    def __init__(self, mensaje: str = "Correo o contraseña incorrectos") -> None:
        super().__init__(mensaje)


class IdentidadNoVerificada(ErrorDominio):
    """El proveedor KYC rechazó el documento (HU-88): la cuenta no se crea."""

    codigo = "identidad_no_verificada"

    def __init__(self, mensaje: str = "No fue posible verificar la identidad") -> None:
        super().__init__(mensaje)


class DependenciaNoDisponible(ErrorDominio):
    codigo = "dependencia_no_disponible"

    def __init__(self, servicio: str) -> None:
        super().__init__(f"No fue posible consultar {servicio}")
