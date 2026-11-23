from __future__ import annotations

import csv
import io
from datetime import date

from app.domain.modelos import Poliza
from app.ports.reportes import ReporteGenerado


def _csv(filas: list[list[str]], encabezado: list[str]) -> str:
    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(encabezado)
    escritor.writerows(filas)
    return buffer.getvalue()


class ReportesStub:
    """HU-62/HU-63: genera el extracto interno en CSV, nunca el formato SFC
    (regulador) ni ACORD (reaseguradora) real -- un prestador real solo
    necesita otro adaptador con este mismo contrato (GeneradorReportes)."""

    async def reporte_regulador(
        self, polizas: list[Poliza], desde: date, hasta: date
    ) -> ReporteGenerado:
        filas = [
            [p.numero, p.estado.value, p.inicio_vigencia.isoformat(), p.fin_vigencia.isoformat(), str(p.prima.valor)]
            for p in polizas
        ]
        contenido = _csv(filas, ["numero", "estado", "inicio_vigencia", "fin_vigencia", "prima"])
        return ReporteGenerado(
            nombre_archivo=f"regulador_{desde.isoformat()}_{hasta.isoformat()}.csv",
            tipo_contenido="text/csv",
            contenido=contenido,
        )

    async def reporte_reaseguradora(
        self, canceladas: list[Poliza], desde: date, hasta: date
    ) -> ReporteGenerado:
        filas = [
            [
                p.numero,
                p.cancelada_en.isoformat() if p.cancelada_en else "",
                p.motivo_cancelacion or "",
                str(p.devolucion_estimada) if p.devolucion_estimada is not None else "0",
            ]
            for p in canceladas
        ]
        contenido = _csv(filas, ["numero", "cancelada_en", "motivo_cancelacion", "devolucion_estimada"])
        return ReporteGenerado(
            nombre_archivo=f"reaseguradora_{desde.isoformat()}_{hasta.isoformat()}.csv",
            tipo_contenido="text/csv",
            contenido=contenido,
        )
