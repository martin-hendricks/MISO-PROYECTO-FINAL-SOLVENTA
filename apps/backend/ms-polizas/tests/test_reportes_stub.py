import csv
import io
from datetime import date, timedelta

from app.domain.modelos import EstadoPoliza
from app.infrastructure.reportes_stub import ReportesStub

from .dobles import poliza_de_prueba


async def test_reporte_regulador_incluye_una_fila_por_poliza():
    stub = ReportesStub()
    desde, hasta = date.today() - timedelta(days=5), date.today()
    polizas = [poliza_de_prueba(), poliza_de_prueba()]

    reporte = await stub.reporte_regulador(polizas, desde, hasta)

    assert reporte.tipo_contenido == "text/csv"
    assert reporte.nombre_archivo == f"regulador_{desde.isoformat()}_{hasta.isoformat()}.csv"
    filas = list(csv.reader(io.StringIO(reporte.contenido)))
    assert filas[0] == ["numero", "estado", "inicio_vigencia", "fin_vigencia", "prima"]
    assert len(filas) == 1 + len(polizas)
    assert filas[1][0] == polizas[0].numero


async def test_reporte_regulador_sin_polizas_solo_tiene_encabezado():
    stub = ReportesStub()
    hoy = date.today()

    reporte = await stub.reporte_regulador([], hoy, hoy)

    filas = list(csv.reader(io.StringIO(reporte.contenido)))
    assert len(filas) == 1


async def test_reporte_reaseguradora_incluye_motivo_y_devolucion():
    stub = ReportesStub()
    hoy = date.today()
    cancelada = poliza_de_prueba(estado=EstadoPoliza.CANCELADA, cancelada_en=hoy)

    reporte = await stub.reporte_reaseguradora([cancelada], hoy, hoy)

    filas = list(csv.reader(io.StringIO(reporte.contenido)))
    assert filas[0] == ["numero", "cancelada_en", "motivo_cancelacion", "devolucion_estimada"]
    assert filas[1][0] == cancelada.numero
    assert filas[1][2] == cancelada.motivo_cancelacion
    assert filas[1][3] == str(cancelada.devolucion_estimada)


async def test_nombre_de_archivo_de_reaseguradora_incluye_el_rango():
    stub = ReportesStub()
    desde, hasta = date(2026, 1, 1), date(2026, 1, 31)

    reporte = await stub.reporte_reaseguradora([], desde, hasta)

    assert reporte.nombre_archivo == "reaseguradora_2026-01-01_2026-01-31.csv"
