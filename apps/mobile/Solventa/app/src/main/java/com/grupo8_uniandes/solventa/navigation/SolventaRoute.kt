package com.grupo8_uniandes.solventa.navigation

import kotlinx.serialization.Serializable

@Serializable
data object InicioRoute

@Serializable
data object CotizacionRoute

@Serializable
data object PolizasRoute

@Serializable
data class PolizaDetalleRoute(val policyId: String = "SOL-0001")

@Serializable
data object SiniestrosRoute

@Serializable
data object PerfilRoute

@Serializable
data class SiniestroDetalleRoute(val claimId: String)

@Serializable
data class EmisionEnCursoRoute(val offerId: String = "")

@Serializable
data object PolizaEmitidaRoute
