package com.grupo8_uniandes.solventa.domain.push

sealed interface PushTarget {
    data class PolizaDetalle(val numero: String) : PushTarget

    data object Inicio : PushTarget
}

fun pushTargetFrom(destino: String?, poliza: String?): PushTarget {
    val numero = poliza?.trim().orEmpty()
    return if (destino == "poliza-detalle" && numero.isNotEmpty()) {
        PushTarget.PolizaDetalle(numero)
    } else {
        PushTarget.Inicio
    }
}
