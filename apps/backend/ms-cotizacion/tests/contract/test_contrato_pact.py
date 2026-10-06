import pytest

pytestmark = pytest.mark.contract


@pytest.mark.skip(reason="HU-88: falta el broker Pact y los pactos de api-socios, bff-web y bff-movil")
def test_ms_cotizacion_cumple_los_pactos_de_sus_consumidores():
    ...
