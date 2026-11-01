package com.grupo8_uniandes.solventa.domain.bff.offer

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

/** Reads the prepared offer again. It does not rate a new price. */
class ShowFirmOffer(
    private val repository: OfferRepository,
) {
    suspend fun load(cotizacionId: String): StandInAnswer<FirmOffer> = repository.requote(cotizacionId)
}
