from app.clients.nucleo import ClienteNucleo


def test_consultas_de_prestadores_omiten_nulos():
    cliente = ClienteNucleo({})
    llamadas = []

    def pedir(servicio, metodo, path, params=None, json=None):
        llamadas.append((servicio, metodo, path, params))
        return {"ok": True}

    cliente._pedir = pedir

    assert cliente.prestadores(pais="CO", ramo=None) == {"ok": True}
    assert llamadas[-1] == ("ms-siniestros", "GET", "/v1/prestadores", {"pais": "CO"})

    cliente.ciudades_prestadores("PE")
    assert llamadas[-1] == (
        "ms-siniestros",
        "GET",
        "/v1/prestadores/ciudades",
        {"pais": "PE", "con_prestadores": "true"},
    )

    cliente.prestadores_siniestro("s-1")
    assert llamadas[-1] == ("ms-siniestros", "GET", "/v1/siniestros/s-1/prestadores", None)

    cliente.prestadores_siniestro("s-1", norte=1, sur=None)
    assert llamadas[-1] == ("ms-siniestros", "GET", "/v1/siniestros/s-1/prestadores", {"norte": 1})
