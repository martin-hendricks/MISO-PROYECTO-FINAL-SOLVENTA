package com.grupo8_uniandes.solventa.quote

import com.grupo8_uniandes.solventa.data.bff.mock.MockOfferRepository
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.DeviceRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteAttempt
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteField
import com.grupo8_uniandes.solventa.domain.bff.offer.RequestFirmOffer
import org.junit.Assert.assertEquals
import org.junit.Test

class RequestFirmOfferTest {
    @Test
    fun givenPublishedAnswers_whenSubmitted_thenThePreparedPremiumReturns() {
        val repository = RecordingOfferRepository()
        val attempt = RequestFirmOffer(repository).submit("2400000", "Pixel", false)
        val ready = (attempt as QuoteAttempt.Answer).answer as StandInAnswer.Ready

        assertEquals("Protección de dispositivo", repository.lastRamo)
        assertEquals(DeviceRisk(2400000, "Pixel", false), repository.lastRisk)
        assertEquals(89000L, ready.value.prima)
        assertEquals("COT-1042", ready.value.cotizacionId)
        assertEquals("COP", ready.value.moneda)
    }

    @Test
    fun givenTheStandIn_whenThePublishedAnswersAreSent_thenItReturnsTheSample() {
        val attempt = RequestFirmOffer(MockOfferRepository()).submit("2400000", "Pixel", false)
        val ready = (attempt as QuoteAttempt.Answer).answer as StandInAnswer.Ready

        assertEquals(89000L, ready.value.prima)
        assertEquals("oferta_vigente", ready.value.estado)
    }

    @Test
    fun givenAMissingAnswer_whenSubmitted_thenTheRepositoryIsNotCalled() {
        val repository = RecordingOfferRepository()
        val request = RequestFirmOffer(repository)

        assertEquals(QuoteField.Value, (request.submit("", "Pixel", false) as QuoteAttempt.Gap).field)
        assertEquals(QuoteField.Value, (request.submit("0", "Pixel", false) as QuoteAttempt.Gap).field)
        assertEquals(QuoteField.Value, (request.submit("-5", "Pixel", false) as QuoteAttempt.Gap).field)
        assertEquals(QuoteField.Value, (request.submit("12.5", "Pixel", false) as QuoteAttempt.Gap).field)
        assertEquals(QuoteField.Brand, (request.submit("2400000", "  ", false) as QuoteAttempt.Gap).field)
        assertEquals(QuoteField.Age, (request.submit("2400000", "Pixel", null) as QuoteAttempt.Gap).field)
        assertEquals(0, repository.quotes)
    }
}

private class RecordingOfferRepository : OfferRepository {
    var quotes: Int = 0
    var lastRamo: String? = null
    var lastRisk: DeviceRisk? = null

    override fun quote(ramo: String, risk: DeviceRisk): StandInAnswer<FirmOffer> {
        quotes += 1
        lastRamo = ramo
        lastRisk = risk
        return StandInAnswer.Ready(
            FirmOffer(
                cotizacionId = "COT-1042",
                ramo = "Protección de dispositivo",
                estado = "oferta_vigente",
                prima = 89000,
                moneda = "COP",
                venceEn = "2026-10-01",
            ),
        )
    }

    override fun requote(cotizacionId: String): StandInAnswer<FirmOffer> = quote("", DeviceRisk(1, "x", false))
}
