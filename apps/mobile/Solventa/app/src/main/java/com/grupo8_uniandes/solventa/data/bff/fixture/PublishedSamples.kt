package com.grupo8_uniandes.solventa.data.bff.fixture

object PublishedSamples {
    const val SESSION_IN = """
        {"correo":"camila@correo.com","contrasena":"********"}
    """

    const val SESSION_OUT = """
        {"accessToken":"jwt","refreshToken":"jwt","expiraEn":900}
    """

    const val REFRESH_IN = """
        {"refreshToken":"jwt"}
    """

    const val SIGNUP = """
        {"nombre":"Camila","apellidos":"Restrepo","documento":"1012345678","correo":"camila@correo.com","pruebaDeVida":"ok","habeasData":true,"ingresos_mensuales":"4500000.00","gastos_mensuales":"1500000.00"}
    """

    const val REVOKE = """
        {"habeasData":false}
    """

    const val OFFER_IN = """
        {"ramo":"Protección de dispositivo","datosRiesgo":{"valorDispositivo":2400000,"marca":"Pixel","masDe12Meses":false,"modelo":"Pixel 8"}}
    """

    const val OFFER_OUT = """
        {"cotizacionId":"COT-1042","ramo":"Protección de dispositivo","estado":"oferta_vigente","prima":89000,"moneda":"COP","venceEn":"2026-10-01"}
    """

    const val REQUOTE_IN = """
        {"cotizacionId":"COT-1042"}
    """

    const val ACCEPT_IN = """
        {"cotizacionId":"COT-1042"}
    """

    const val ISSUED = """
        {"numero":"POL-88219-CO","ramo":"Protección de dispositivo","estado":"vigente","venceEn":"2027-03-12"}
    """

    const val REJECTION = """
        {"estado":"rechazada","motivo":"La suscripción automática rechazó el riesgo del dispositivo cotizado."}
    """

    const val WALLET = """
        {"polizas":[{"numero":"POL-88219-CO","ramo":"Protección de dispositivo","resumen":"Robo, Pantalla, Hurto","estado":"vigente","venceEn":"2027-03-12","inicioVigencia":"2026-03-12","finVigencia":"2027-03-12","moneda":"COP","primaTotal":89000},{"numero":"POL-11002-CO","ramo":"Microseguro de vida","resumen":"amparo de vida","estado":"por_vencer","venceEn":"2026-11-06","inicioVigencia":"2025-11-06","finVigencia":"2026-11-06","moneda":"COP","primaTotal":42000}]}
    """

    const val DETAIL = """
        {"numero":"POL-88219-CO","ramo":"Protección de dispositivo","resumen":"Robo y Pantalla","estado":"vigente","venceEn":"2027-03-12","inicioVigencia":"2026-03-12","finVigencia":"2027-03-12","moneda":"COP","primaTotal":89000,"coberturas":[{"nombre":"Robo","sumaAsegurada":4000000,"deducible":0},{"nombre":"Pantalla","sumaAsegurada":1500000,"deducible":150000}],"queHacer":"Si se rompe la pantalla o te roban el equipo: toma la foto del daño, anota fecha y lugar, y no repares antes de dar el aviso. Cada ramo pide una evidencia distinta.","renovable":true,"renovacionAutomatica":false}
    """

    const val CLAIM_DETAIL = """
        {"id":"interno","siniestroId":"SIN-441","tipo":"asistido","ramo":"Protección de dispositivo","poliza":"POL-88219-CO","resumen":"pantalla rota","fecha":"2026-03-12","estado":"decidido","resultado":"rechazado","estadoTexto":"Decidido","reserva":350000,"moneda":"COP","descripcion":"Pantalla rota al caer el teléfono","lugar":"Av. Caracas con Calle 72","geo":{"lat":4.6533,"lng":-74.0836,"precisionM":12},"motivo":"Póliza no vigente en la fecha del hecho","evidencia":[{"nombre":"dano.jpg","tipo":"foto","contentType":"image/png","url":"https://example.test/dano.jpg"}],"historial":[{"estado":"recibido","fecha":"2026-03-12T10:00:00","estadoTexto":"Recibido"},{"estado":"decidido","fecha":"2026-03-13T10:00:00","estadoTexto":"Decidido"}],"pago":null,"umbral":null}
    """

    const val CLAIM_NOTICE = """
        {"poliza":"POL-88219-CO","fechaHecho":"2026-03-12","geo":{"lat":4.6533,"lng":-74.0836,"precisionM":12},"adjuntos":[{"tipo":"foto","nombre":"dano.jpg"},{"tipo":"video","nombre":"dano.mp4"},{"tipo":"recibo","nombre":"recibo.jpg"},{"tipo":"soporte","nombre":"acta.jpg"}]}
    """

    const val CLAIM_NOTICE_NO_GEO = """
        {"poliza":"POL-88219-CO","fechaHecho":"2026-03-12","geo":null,"adjuntos":[{"tipo":"foto","nombre":"dano.jpg"}]}
    """

    const val CLAIM_RECEIPT = """
        {"siniestroId":"SIN-441","estado":"recibido"}
    """

    const val CLAIMS = """
        {"siniestros":[{"siniestroId":"SIN-441","ramo":"Protección de dispositivo","resumen":"pantalla rota","estado":"en_evaluacion","poliza":"POL-88219-CO"},{"siniestroId":"SIN-220","ramo":"Protección de dispositivo","resumen":"hurto","estado":"pagado","poliza":"POL-88219-CO"},{"siniestroId":"SIN-P01","ramo":"Clima y vuelos","resumen":"retraso de vuelo","estado":"pagado","estadoTexto":"Pago automático · pagado","poliza":"POL-11002-CO"}]}
    """

    const val PAYMENT = """
        {"siniestroId":"SIN-220","poliza":"POL-11002-CO","umbral":"retraso mayor a 120 min","monto":250000,"moneda":"COP","estado":"pagado"}
    """

    const val MORTGAGE_IN = """
        {"credito":{"valor":180000000,"plazoMeses":180},"consentimientoPerfil":true}
    """

    const val MORTGAGE_OUT = """
        {"ramo":"Vida hipotecario","estado":"oferta_vigente","prima":64000,"moneda":"COP","factores":["plazo","valor del crédito"],"degradada":false}
    """

    const val PROFILING_CONSENT = """
        {"estado":"vigente","otorgadoEn":"2026-10-01T10:00:00Z"}
    """

    const val PROFILING_CONSENT_REVOKED = """
        {"estado":"revocado","revocadoEn":"2026-11-11T15:30:00Z"}
    """

    const val MORTGAGE_DEGRADED = """
        {"ramo":"Vida hipotecario","estado":"oferta_vigente","prima":64000,"moneda":"COP","factores":["plazo","valor del crédito"],"degradada":true}
    """

    const val NOTICES = """
        {"avisos":[{"tipo":"vencimiento","poliza":"POL-88219-CO","venceEn":"2027-03-12"},{"tipo":"renovacion","poliza":"POL-88219-CO","estado":"vigente"}]}
    """

    const val RENEW = """
        {"numero":"POL-88219-CO","verbo":"renovar"}
    """

    const val CANCEL = """
        {"numero":"POL-88219-CO","verbo":"cancelar","motivo":"El cliente lo pidió"}
    """

    const val CANCEL_NO_REASON = """
        {"numero":"POL-88219-CO","verbo":"cancelar"}
    """

    const val HOME = """
        {"ofertaVigente":{"cotizacionId":"COT-1042","ramo":"Protección de dispositivo","estado":"oferta_vigente"},"poliza":{"numero":"POL-88219-CO","ramo":"Protección de dispositivo","estado":"vigente"},"siniestroEnCurso":{"siniestroId":"SIN-441","estado":"en_evaluacion"},"hipotecario":null}
    """

    const val PUSH_REGISTRATION = """
        {"token":"fcm-stub","plataforma":"android"}
    """

    const val PUSH_NOTICE = """
        {"tipo":"vencimiento","titulo":"Tu póliza vence","cuerpo":"En 7 días","destino":"aviso-vencimiento","poliza":"POL-88219-CO"}
    """

    const val PARAMETRIC_PUSH = """
        {"tipo":"pago_automatico","titulo":"Pago automático realizado","cuerpo":"Retraso > 90 min · dato oficial del vuelo","destino":"parametrico","poliza":"POL-88219-CO"}
    """

    const val PROVIDERS = """
        {"prestadores":[{"id":"PR-1","nombre":"Taller Norte","distanciaKm":1.2,"zona":"Chapinero"},{"id":"PR-2","nombre":"Taller Sur","distanciaKm":3.4,"zona":"Kennedy"}]}
    """

    const val ASSISTANCE_IN = """
        {"prestadorId":"PR-1","geo":{"lat":4.6533,"lng":-74.0836},"poliza":"POL-88219-CO"}
    """

    const val ASSISTANCE_OUT = """
        {"asistenciaId":"AS-18","estado":"registrada"}
    """
}
