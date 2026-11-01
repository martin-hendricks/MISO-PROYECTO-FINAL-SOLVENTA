package com.grupo8_uniandes.solventa.quote

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteInput
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteLine
import com.grupo8_uniandes.solventa.domain.bff.offer.RequestFirmOffer
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class QuoteViewModelTest {
    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

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
                    override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> {
                        sent = ramo
                        return StandInAnswer.Ready(sample().copy(ramo = ramo))
                    }

                    override suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer> =
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

    @Test
    fun givenEachAnswer_whenTyped_thenThatFieldKeepsTheText() {
        val viewModel = filled(scripted(StandInAnswer.Failed))
        viewModel.onMenu(true)
        assertTrue(viewModel.state.value.menuOpen)
        viewModel.onMenu(false)
        val beforeAge = viewModel.state.value.value
        viewModel.onText(QuoteInput.Age, "ignored")
        assertEquals(beforeAge, viewModel.state.value.value)

        val typed = listOf(
            QuoteInput.SumInsured to { state: QuoteUiState -> state.sumInsured },
            QuoteInput.AgeYears to { state: QuoteUiState -> state.ageYears },
            QuoteInput.Event to { state: QuoteUiState -> state.event },
            QuoteInput.Reference to { state: QuoteUiState -> state.reference },
            QuoteInput.Threshold to { state: QuoteUiState -> state.threshold },
            QuoteInput.CreditValue to { state: QuoteUiState -> state.creditValue },
            QuoteInput.CreditTerm to { state: QuoteUiState -> state.creditTerm },
            QuoteInput.Installment to { state: QuoteUiState -> state.installment },
            QuoteInput.Term to { state: QuoteUiState -> state.term },
            QuoteInput.Destination to { state: QuoteUiState -> state.destination },
            QuoteInput.Duration to { state: QuoteUiState -> state.duration },
            QuoteInput.Value to { state: QuoteUiState -> state.value },
            QuoteInput.Brand to { state: QuoteUiState -> state.brand },
        )
        typed.forEach { (input, read) ->
            viewModel.onText(input, input.name)
            assertEquals(input.name, read(viewModel.state.value))
            assertNull(viewModel.state.value.gap)
        }
    }

    @Test
    fun givenASuspendingAsk_whenCotizar_thenWaitingComesBeforeTheResult() {
        val success = CompletableDeferred<StandInAnswer<FirmOffer>>()
        val viewModel = filled(gated(success))

        viewModel.cotizar()

        assertTrue(viewModel.state.value.pending)
        assertFalse(viewModel.state.value.failed)
        success.complete(StandInAnswer.Ready(sample()))
        assertEquals("COT-1042", viewModel.state.value.readyId)
        assertFalse(viewModel.state.value.pending)

        val failure = CompletableDeferred<StandInAnswer<FirmOffer>>()
        val failed = filled(gated(failure))
        failed.cotizar()
        assertTrue(failed.state.value.pending)
        assertFalse(failed.state.value.failed)
        failure.complete(StandInAnswer.Failed)
        assertTrue(failed.state.value.failed)
        assertNull(failed.state.value.readyId)
        assertFalse(failed.state.value.pending)
    }

    private fun gated(gate: CompletableDeferred<StandInAnswer<FirmOffer>>) = object : OfferRepository {
        override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> = gate.await()

        override suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer> = StandInAnswer.Failed
    }

    private fun scripted(answer: StandInAnswer<FirmOffer>) = object : OfferRepository {
        override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> = answer

        override suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer> = answer
    }
}
