"""Vocabulario canónico de ramos compartido por los canales."""

SIN_CLASIFICAR = "Sin clasificar"

PRODUCTOS: dict[str, tuple[str, str]] = {
    "proteccion-dispositivo": (
        "Protección de dispositivo",
        "Cubre robo, daño accidental y reposición del equipo asegurado.",
    ),
    "soat-motocicleta": (
        "SOAT motocicleta",
        "Cubre la atención de víctimas de un accidente de tránsito en motocicleta.",
    ),
    "microseguro-de-vida": (
        "Microseguro de vida",
        "Cubre a la persona asegurada según la suma y la edad declaradas.",
    ),
    "clima-y-vuelos": (
        "Clima y vuelos",
        "Cubre un evento climático o de vuelo cuando se supera el umbral.",
    ),
    "vida-hipotecario": (
        "Vida hipotecario",
        "Cubre el saldo del crédito hipotecario durante el plazo pactado.",
    ),
    "pagos": (
        "Pagos",
        "Cubre las cuotas del plan de pagos durante el plazo declarado.",
    ),
    "viaje": (
        "Viaje",
        "Cubre el viaje según el destino y la duración declarados.",
    ),
    "vida-crediticia": (
        "Vida crediticia",
        "Cubre el saldo del crédito ante muerte o incapacidad total.",
    ),
}


def producto_de(ramo: str) -> str | None:
    for codigo, (nombre, _) in PRODUCTOS.items():
        if ramo in {codigo, nombre}:
            return codigo
    return None


def presentar(producto: str | None) -> tuple[str, str]:
    if producto and producto in PRODUCTOS:
        return PRODUCTOS[producto]
    return SIN_CLASIFICAR, ""
