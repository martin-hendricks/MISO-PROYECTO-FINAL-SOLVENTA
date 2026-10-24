package com.grupo8_uniandes.solventa.domain.bff.offer

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

sealed interface LineRisk

data class DeviceRisk(
    val valorDispositivo: Long,
    val marca: String,
    val masDe12Meses: Boolean,
) : LineRisk

data class FirmOffer(
    val cotizacionId: String,
    val ramo: String,
    val estado: String,
    val prima: Long,
    val moneda: String,
    val venceEn: String,
)

interface OfferRepository {
    suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer>

    suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer>
}
