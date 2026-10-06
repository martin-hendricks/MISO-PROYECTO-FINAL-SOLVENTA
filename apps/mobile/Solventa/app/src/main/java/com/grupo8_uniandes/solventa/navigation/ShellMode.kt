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
        InicioRoute, PolizasRoute, SiniestrosRoute, PerfilRoute -> ShellMode.Root
        CotizacionRoute, is PolizaDetalleRoute -> ShellMode.Nested
        else -> ShellMode.Root
    }
}

fun selectedDestination(route: Any): Destination? = when (route) {
    InicioRoute, CotizacionRoute -> Destination.Inicio
    PolizasRoute, is PolizaDetalleRoute -> Destination.Polizas
    SiniestrosRoute -> Destination.Siniestros
    PerfilRoute -> Destination.Perfil
    else -> null
}
