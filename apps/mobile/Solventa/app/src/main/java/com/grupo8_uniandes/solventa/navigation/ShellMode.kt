package com.grupo8_uniandes.solventa.navigation

enum class ShellMode {
    PreLogin,
    Root,
    Nested,
    Issuance,
}

fun shellMode(route: Any, signedIn: Boolean): ShellMode {
    if (!signedIn) return ShellMode.PreLogin
    if (route is EmisionEnCursoRoute || route is PolizaEmitidaRoute) return ShellMode.Issuance
    return when (route) {
        InicioRoute, PolizasRoute, SiniestrosRoute, MapaPrestadoresRoute, PerfilRoute -> ShellMode.Root
        is CotizacionRoute, is VerOfertaRoute, is PolizaDetalleRoute, is SiniestroDetalleRoute,
        AsistenciaSitioRoute, SuscripcionRechazadaRoute, OfertaHipotecarioRoute,
        AvisoSiniestroRoute, EvidenciaAvisoRoute, is ConfirmacionAvisoRoute,
        ParametricoRoute, AvisoVencimientoRoute, AvisoRenovacionRoute,
        -> ShellMode.Nested
        else -> ShellMode.Root
    }
}

fun selectedDestination(route: Any): Destination? = when (route) {
    InicioRoute, is CotizacionRoute, is VerOfertaRoute, SuscripcionRechazadaRoute,
    OfertaHipotecarioRoute,
    -> Destination.Inicio
    PolizasRoute, is PolizaDetalleRoute, AvisoVencimientoRoute, AvisoRenovacionRoute,
    -> Destination.Polizas
    SiniestrosRoute, MapaPrestadoresRoute, AsistenciaSitioRoute, AvisoSiniestroRoute,
    EvidenciaAvisoRoute, is ConfirmacionAvisoRoute, is SiniestroDetalleRoute,
    ParametricoRoute,
    -> Destination.Siniestros
    PerfilRoute -> Destination.Perfil
    else -> null
}
