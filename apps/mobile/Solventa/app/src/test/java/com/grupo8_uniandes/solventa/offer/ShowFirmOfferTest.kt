package com.grupo8_uniandes.solventa.offer

import com.grupo8_uniandes.solventa.data.bff.mock.MockOfferRepository
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.ShowFirmOffer
import org.junit.Assert.assertEquals
import org.junit.Test

class ShowFirmOfferTest {
    @Test
    fun givenPublishedOffer_whenOpenedTwice_thenPremiumStays() {
        val show = ShowFirmOffer(MockOfferRepository())

        val first = show.load("COT-1042") as StandInAnswer.Ready
        val second = show.load("COT-1042") as StandInAnswer.Ready

        assertEquals("COT-1042", first.value.cotizacionId)
        assertEquals("Protección de dispositivo", first.value.ramo)
        assertEquals("oferta_vigente", first.value.estado)
        assertEquals(89000L, first.value.prima)
        assertEquals("COP", first.value.moneda)
        assertEquals("2026-10-01", first.value.venceEn)
        assertEquals(first.value.prima, second.value.prima)
        assertEquals(first.value.moneda, second.value.moneda)
        assertEquals(first.value.venceEn, second.value.venceEn)
    }
}
