from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "db"
HISTORICA = RAIZ / "05_ms_cotizacion_catalogo.sql"
NUEVA = RAIZ / "10_ms_cotizacion_multiramo.sql"


def test_la_migracion_historica_no_cambia_el_contrato_original():
    texto = HISTORICA.read_text()
    assert "texto" not in texto
    assert "booleano" not in texto
    assert "descripcion" not in texto


def test_la_migracion_nueva_agrega_los_tipos_de_riesgo():
    texto = NUEVA.read_text()
    assert "ADD COLUMN IF NOT EXISTS descripcion" in texto
    assert "'texto'" in texto
    assert "'booleano'" in texto


def test_una_base_nueva_y_una_ya_migrada_aceptan_el_mismo_script():
    """05 is the historical catalog. 10 is the only delta and can run twice."""
    historica = HISTORICA.read_text()
    nueva = NUEVA.read_text()
    assert "CREATE TABLE" in historica
    assert "ADD COLUMN IF NOT EXISTS descripcion" in nueva
    assert "DROP CONSTRAINT IF EXISTS" in nueva
    assert "AND NOT EXISTS" in nueva
    assert nueva.count("INSERT INTO ms_cotizacion.dato_riesgo_producto") >= 2
