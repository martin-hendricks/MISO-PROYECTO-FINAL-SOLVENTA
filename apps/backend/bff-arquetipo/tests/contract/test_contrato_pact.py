import pytest

pytestmark = pytest.mark.contract


@pytest.mark.skip(reason="HU-88: falta el broker Pact y los pactos de los consumidores")
def test_bff_cumple_el_pacto_del_consumidor():
    ...
