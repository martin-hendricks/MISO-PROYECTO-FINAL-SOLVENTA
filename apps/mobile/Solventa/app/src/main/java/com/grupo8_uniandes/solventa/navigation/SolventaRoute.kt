package com.grupo8_uniandes.solventa.navigation

import kotlinx.serialization.Serializable

@Serializable
data object InicioRoute

@Serializable
data class CotizacionRoute(val cotizacionId: String = "")

@Serializable
data class VerOfertaRoute(val cotizacionId: String)

@Serializable
data object PolizasRoute

@Serializable
data class PolizaDetalleRoute(val policyId: String = "SOL-0001")

@Serializable
data object SiniestrosRoute

@Serializable
data object MapaPrestadoresRoute

@Serializable
data object AsistenciaSitioRoute

@Serializable
data object PerfilRoute

@Serializable
data class SiniestroDetalleRoute(val claimId: String)

@Serializable
data class EmisionEnCursoRoute(val offerId: String = "")

@Serializable
data class PolizaEmitidaRoute(val numero: String = "POL-88219-CO")

@Serializable
data object SuscripcionRechazadaRoute

@Serializable
data object OfertaHipotecarioRoute
