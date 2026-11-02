package com.grupo8_uniandes.solventa.offer

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.ShowFirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.formatOfferDate
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.math.BigDecimal

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class OfferViewModelTest {
    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenPublishedOffer_whenLoadedTwice_thenAcceptStaysEnabledOnTheSamePremium() {
        val viewModel = offerModel(published())

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
        val state = offerModel(StandInAnswer.Pending).state.value

        assertEquals(OfferPhase.Pending, state.phase)
        assertFalse(state.acceptEnabled)
    }

    @Test
    fun givenFailure_whenLoaded_thenTheSampleIsAbsent() {
        val state = offerModel(StandInAnswer.Failed).state.value

        assertEquals(OfferPhase.Failed, state.phase)
        assertEquals("", state.premiumText)
        assertFalse(state.acceptEnabled)
    }

    @Test
    fun givenExpiredReading_whenLoaded_thenPremiumStaysAndAcceptIsDisabled() {
        val expired = published().copy(estado = "oferta_vencida")
        val state = offerModel(expired).state.value

        assertEquals(formatPremium(BigDecimal("89000"), "COP", Region.Colombia), state.premiumText)
        assertTrue(state.expired)
        assertFalse(state.acceptEnabled)
    }

    @Test
    fun givenInForce_whenTheEndDateIsPast_thenAcceptStaysEnabled() {
        val state = offerModel(published()).state.value

        assertEquals("oferta_vigente", published().estado)
        assertTrue(state.acceptEnabled)
        assertFalse(state.expired)
    }

    @Test
    fun givenAQuotedOffer_whenLoaded_thenAcceptIsEnabledOnTheUtcDay() {
        val quoted = published().copy(
            estado = "cotizada",
            prima = 106900,
            venceEn = "2026-11-02T02:00:23.185686Z",
        )
        val state = offerModel(quoted).state.value

        assertEquals(OfferPhase.Ready, state.phase)
        assertTrue(state.acceptEnabled)
        assertFalse(state.expired)
        assertEquals(formatPremium(BigDecimal("106900"), "COP", Region.Colombia), state.premiumText)
        assertEquals(formatOfferDate("2026-11-02", Region.Colombia), state.endDateText)
        assertEquals(formatOfferDate("2026-11-02T02:00:23.185686Z", Region.Colombia), state.endDateText)
    }

    @Test
    fun givenAnotherStatus_whenLoaded_thenAcceptIsDisabledWithoutTheExpiredSentence() {
        val state = offerModel(published().copy(estado = "usada")).state.value

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

    private fun offerModel(offer: FirmOffer) = offerModel(StandInAnswer.Ready(offer))

    private fun offerModel(answer: StandInAnswer<FirmOffer>): OfferViewModel {
        val repo = scripted(answer)
        return OfferViewModel(ShowFirmOffer(repo), "COT-1042")
    }

    private fun scripted(answer: StandInAnswer<FirmOffer>) = object : OfferRepository {
        override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> = answer

        override suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer> = answer

        override suspend fun accept(cotizacionId: String) = StandInAnswer.Failed
    }
}
