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
        {"nombre":"Camila","apellidos":"Restrepo","documento":"1012345678","correo":"camila@correo.com","pruebaDeVida":"ok","habeasData":true}
    """

    const val REVOKE = """
        {"habeasData":false}
    """

    const val OFFER_IN = """
        {"ramo":"Protección de dispositivo","datosRiesgo":{"valorDispositivo":2400000,"marca":"Pixel","masDe12Meses":false}}
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
        {"estado":"rechazada","motivo":"Valor del equipo fuera de rango"}
    """

    const val WALLET = """
        {"polizas":[{"numero":"POL-88219-CO","ramo":"Protección de dispositivo","resumen":"Robo, Pantalla, Hurto","estado":"vigente","venceEn":"2027-03-12"}]}
    """

    const val DETAIL = """
        {"numero":"POL-88219-CO","ramo":"Protección de dispositivo","resumen":"Robo y Pantalla","estado":"vigente","venceEn":"2027-03-12","queHacer":"Toma la foto del daño y anota fecha y lugar."}
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
        {"siniestros":[{"siniestroId":"SIN-441","ramo":"Protección de dispositivo","resumen":"Pantalla rota","estado":"en_evaluacion"}]}
    """

    const val PAYMENT = """
        {"siniestroId":"SIN-220","poliza":"POL-11002-CO","umbral":"retraso mayor a 120 min","monto":250000,"moneda":"COP","estado":"pagado"}
    """

    const val MORTGAGE_IN = """
        {"credito":{"valor":180000000,"plazoMeses":180},"consentimientoPerfil":true}
    """

    const val MORTGAGE_OUT = """
        {"ramo":"Vida crediticia","estado":"oferta_vigente","prima":64000,"moneda":"COP","factores":["plazo","valor del crédito"],"degradada":false}
    """

    const val MORTGAGE_DEGRADED = """
        {"ramo":"Vida crediticia","estado":"oferta_vigente","prima":64000,"moneda":"COP","factores":["plazo","valor del crédito"],"degradada":true}
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
