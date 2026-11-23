from app.domain.evento import EventoTelemetria


class PublicadorEnMemoria:
    """Sin bus configurado (pruebas y desarrollo): guarda los eventos en una lista."""

    def __init__(self) -> None:
        self.publicados: list[EventoTelemetria] = []

    async def publicar(self, evento: EventoTelemetria) -> None:
        self.publicados.append(evento)

    def listo(self) -> bool:
        return True
