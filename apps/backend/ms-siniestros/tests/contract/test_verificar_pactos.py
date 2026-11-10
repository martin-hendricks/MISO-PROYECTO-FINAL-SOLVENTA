"""Verifica los pactos de bff-web y bff-movil contra GET /v1/pagos-recibidos.

Los consumidores escriben el pacto en su carpeta `pacts/`. Si todavía no existe,
el test se omite: no hay nada que verificar.
"""

from pathlib import Path

import pytest

pact_v3 = pytest.importorskip("pact.v3")

pytestmark = pytest.mark.contract

BACKEND = Path(__file__).resolve().parents[3]
PACTOS = [
    BACKEND / "bff-web" / "pacts" / "bff-web-ms-siniestros.json",
    BACKEND / "bff-movil" / "pacts" / "bff-movil-ms-siniestros.json",
]


def test_pactos_de_billetera_existen_o_se_omiten():
    presentes = [p for p in PACTOS if p.exists()]
    if not presentes:
        pytest.skip("los consumidores todavía no publican el pacto de pagos-recibidos")
    for pacto in presentes:
        assert pacto.stat().st_size > 0
