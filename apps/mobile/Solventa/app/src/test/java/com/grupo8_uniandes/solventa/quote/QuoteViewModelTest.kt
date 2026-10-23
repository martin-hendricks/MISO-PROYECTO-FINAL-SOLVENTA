package com.grupo8_uniandes.solventa.quote

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteInput
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteLine
import com.grupo8_uniandes.solventa.domain.bff.offer.RequestFirmOffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class QuoteViewModelTest {
    @Test
    fun givenPublishedAnswers_whenCotizar_thenReadyCarriesTheQuoteId() {
        val viewModel = QuoteViewModel(RequestFirmOffer(scripted(StandInAnswer.Ready(sample()))), "COT-1042")
        viewModel.onValue("2400000")
        viewModel.onBrand("Pixel")
        viewModel.onAge(false)

        viewModel.cotizar()

        assertEquals("COT-1042", viewModel.state.value.readyId)
        viewModel.consumeReady()
        assertNull(viewModel.state.value.readyId)
        assertEquals("COT-1042", viewModel.state.value.contextId)
        assertFalse(viewModel.state.value.pending)
        assertFalse(viewModel.state.value.failed)
    }

    @Test
    fun givenPending_whenCotizar_thenItIsProgressNotFailure() {
        val viewModel = filled(scripted(StandInAnswer.Pending))

        viewModel.cotizar()

        assertTrue(viewModel.state.value.pending)
        assertFalse(viewModel.state.value.failed)
        assertNull(viewModel.state.value.readyId)
    }

    @Test
    fun givenFailure_whenCotizar_thenItStaysOnTheForm() {
        val viewModel = filled(scripted(StandInAnswer.Failed))

        viewModel.cotizar()

        assertTrue(viewModel.state.value.failed)
        assertFalse(viewModel.state.value.pending)
        assertNull(viewModel.state.value.readyId)
    }

    @Test
    fun givenAGap_whenCotizar_thenNothingIsReady() {
        val viewModel = QuoteViewModel(RequestFirmOffer(scripted(StandInAnswer.Ready(sample()))))

        viewModel.cotizar()

        assertEquals(QuoteInput.Value, viewModel.state.value.gap)
        assertNull(viewModel.state.value.readyId)
    }

    @Test
    fun givenDeviceAnswers_whenTheLineChangesToTravel_thenThoseAnswersClear() {
        val viewModel = filled(scripted(StandInAnswer.Ready(sample())))

        viewModel.onLine(QuoteLine.Travel)

        assertEquals(QuoteLine.Travel, viewModel.state.value.line)
        assertEquals("", viewModel.state.value.value)
        assertEquals("", viewModel.state.value.brand)
        assertNull(viewModel.state.value.olderThan12Months)
        assertFalse(viewModel.state.value.menuOpen)
    }

    @Test
    fun givenTravelAnswers_whenCotizar_thenTheRequestUsesThatLine() {
        var sent: String? = null
        val viewModel = QuoteViewModel(
            RequestFirmOffer(
                object : OfferRepository {
                    override fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> {
                        sent = ramo
                        return StandInAnswer.Ready(sample().copy(ramo = ramo))
                    }

                    override fun requote(cotizacionId: String): StandInAnswer<FirmOffer> =
                        StandInAnswer.Failed
                },
            ),
        )
        viewModel.onLine(QuoteLine.Travel)
        viewModel.onText(QuoteInput.Destination, "Bogotá")
        viewModel.onText(QuoteInput.Duration, "7")

        viewModel.cotizar()

        assertEquals("Viaje", sent)
        assertEquals("COT-1042", viewModel.state.value.readyId)
    }

    @Test
    fun givenAResult_whenCancel_thenItDoesNotAcceptAndKeepsContext() {
        val viewModel = filled(scripted(StandInAnswer.Ready(sample())), "COT-1042")
        viewModel.cotizar()

        viewModel.cancel()

        assertNull(viewModel.state.value.readyId)
        assertEquals("", viewModel.state.value.value)
        assertEquals("COT-1042", viewModel.state.value.contextId)
    }

    private fun filled(repository: OfferRepository, contextId: String = "") : QuoteViewModel {
        return QuoteViewModel(RequestFirmOffer(repository), contextId).apply {
            onValue("2400000")
            onBrand("Pixel")
            onAge(false)
        }
    }

    private fun sample() = FirmOffer(
        cotizacionId = "COT-1042",
        ramo = "Protección de dispositivo",
        estado = "oferta_vigente",
        prima = 89000,
        moneda = "COP",
        venceEn = "2026-10-01",
    )

    private fun scripted(answer: StandInAnswer<FirmOffer>) = object : OfferRepository {
        override fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> = answer

        override fun requote(cotizacionId: String): StandInAnswer<FirmOffer> = answer
    }
}
