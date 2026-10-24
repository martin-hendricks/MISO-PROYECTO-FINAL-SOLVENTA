package com.grupo8_uniandes.solventa.domain.bff.offer

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

data class DeviceRisk(
    val valorDispositivo: Long,
    val marca: String,
    val masDe12Meses: Boolean,
)

data class FirmOffer(
    val cotizacionId: String,
    val ramo: String,
    val estado: String,
    val prima: Long,
    val moneda: String,
    val venceEn: String,
)

interface OfferRepository {
    fun quote(ramo: String, risk: DeviceRisk): StandInAnswer<FirmOffer>

    fun requote(cotizacionId: String): StandInAnswer<FirmOffer>
}
