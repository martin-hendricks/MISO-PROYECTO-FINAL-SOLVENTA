package com.grupo8_uniandes.solventa.offer

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.DeviceRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.ShowFirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.formatOfferDate
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.math.BigDecimal

class OfferViewModelTest {
    @Test
    fun givenPublishedOffer_whenLoadedTwice_thenAcceptStaysEnabledOnTheSamePremium() {
        val viewModel = OfferViewModel(ShowFirmOffer(scripted(published())), "COT-1042")

        val first = viewModel.state.value
        viewModel.refresh()
        val second = viewModel.state.value

        assertEquals(OfferPhase.Ready, first.phase)
        assertEquals(formatPremium(BigDecimal("89000"), "COP", Region.Colombia), first.premiumText)
        assertEquals(formatOfferDate("2026-10-01", Region.Colombia), first.endDateText)
        assertNotEquals("2026-10-01", first.endDateText)
        assertTrue(first.acceptEnabled)
        assertFalse(first.expired)
        assertEquals("COT-1042", first.cotizacionId)
        assertEquals(first.premiumText, second.premiumText)
    }

    @Test
    fun givenPending_whenLoaded_thenItIsNotAFailure() {
        val state = OfferViewModel(ShowFirmOffer(scripted(StandInAnswer.Pending)), "COT-1042").state.value

        assertEquals(OfferPhase.Pending, state.phase)
        assertFalse(state.acceptEnabled)
    }

    @Test
    fun givenFailure_whenLoaded_thenTheSampleIsAbsent() {
        val state = OfferViewModel(ShowFirmOffer(scripted(StandInAnswer.Failed)), "COT-1042").state.value

        assertEquals(OfferPhase.Failed, state.phase)
        assertEquals("", state.premiumText)
        assertFalse(state.acceptEnabled)
    }

    @Test
    fun givenExpiredReading_whenLoaded_thenPremiumStaysAndAcceptIsDisabled() {
        val expired = published().copy(estado = "oferta_vencida")
        val state = OfferViewModel(ShowFirmOffer(scripted(expired)), "COT-1042").state.value

        assertEquals(formatPremium(BigDecimal("89000"), "COP", Region.Colombia), state.premiumText)
        assertTrue(state.expired)
        assertFalse(state.acceptEnabled)
    }

    @Test
    fun givenInForce_whenTheEndDateIsPast_thenAcceptStaysEnabled() {
        val state = OfferViewModel(ShowFirmOffer(scripted(published())), "COT-1042").state.value

        assertEquals("oferta_vigente", published().estado)
        assertTrue(state.acceptEnabled)
        assertFalse(state.expired)
    }

    @Test
    fun givenAnotherStatus_whenLoaded_thenAcceptIsDisabledWithoutTheExpiredSentence() {
        val state = OfferViewModel(
            ShowFirmOffer(scripted(published().copy(estado = "usada"))),
            "COT-1042",
        ).state.value

        assertFalse(state.acceptEnabled)
        assertFalse(state.expired)
    }

    private fun published() = FirmOffer(
        cotizacionId = "COT-1042",
        ramo = "Protección de dispositivo",
        estado = "oferta_vigente",
        prima = 89000,
        moneda = "COP",
        venceEn = "2026-10-01",
    )

    private fun scripted(offer: FirmOffer) = scripted(StandInAnswer.Ready(offer))

    private fun scripted(answer: StandInAnswer<FirmOffer>) = object : OfferRepository {
        override fun quote(ramo: String, risk: DeviceRisk): StandInAnswer<FirmOffer> = answer

        override fun requote(cotizacionId: String): StandInAnswer<FirmOffer> = answer
    }
}
