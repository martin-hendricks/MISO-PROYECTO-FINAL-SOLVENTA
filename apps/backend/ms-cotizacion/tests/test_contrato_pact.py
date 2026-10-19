import pytest


@pytest.mark.contract
def test_contrato_post_cotizaciones_pendiente():
    """Contrato esperado de POST /v1/cotizaciones para quien tome HU-88 (instalar Pact
    en el MVP, ver wiki Estrategia-de-pruebas, PI-01):

    - Consumidores: :BFFWeb, :BFFMovil, :APISocios.
    - Request: SolicitarCotizacionEntrada (usuario_id, socio_id, consentimiento_id,
      producto, canal, datos_riesgo), header Idempotency-Key obligatorio.
    - Response 201/200: CotizacionSalida — en HU-96 solo cotizacion_id/estado/producto/
      creada_en; desde HU-99 incluye además prima, prima_neta, gastos_expedicion, moneda,
      vence_en, factor_riesgo_origen; desde HU-100 también vencida en el GET.
    - Response 422: ErrorSalida (codigo, mensaje) para producto_no_encontrado,
      dato_riesgo_faltante, dato_riesgo_fuera_de_rango, insumo_obligatorio_ausente.

    No hay ningún ejemplo de Pact real implementado en el repo todavía (solo este marker).
    """
    pytest.skip("Pact pendiente — fuera de alcance de HU-96, corresponde a HU-88")
