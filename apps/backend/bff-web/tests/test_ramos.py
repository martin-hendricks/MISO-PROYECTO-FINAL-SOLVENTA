from app.ramos import presentar


def test_presentar_acepta_el_codigo_y_el_nombre_de_vida_hipotecario():
    assert presentar("vida-hipotecario")[0] == "Vida hipotecario"
    assert presentar("Vida hipotecario")[0] == "Vida hipotecario"


def test_presentar_sin_producto_queda_sin_clasificar():
    assert presentar(None)[0] == "Sin clasificar"
    assert presentar("ramo-desconocido")[0] == "Sin clasificar"
