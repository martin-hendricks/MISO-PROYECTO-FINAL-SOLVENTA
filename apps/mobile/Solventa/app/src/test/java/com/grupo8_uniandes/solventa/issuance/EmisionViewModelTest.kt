package com.grupo8_uniandes.solventa.issuance

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.AcceptedQuote
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class EmisionViewModelTest {
    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenAceptada_whenTheScreenOpens_thenTheIdIsReady() {
        val accepted = AcceptedQuote("COT-9", "aceptada", 10, "COP")
        val viewModel = EmisionViewModel(scripted(StandInAnswer.Ready(accepted)), "COT-9")

        assertEquals(EmisionPhase.Issued, viewModel.state.value.phase)
        assertEquals("COT-9", viewModel.state.value.cotizacionId)
    }

    @Test
    fun givenAFailure_whenTheScreenOpens_thenItIsRejectedWithoutAnId() {
        val viewModel = EmisionViewModel(scripted(StandInAnswer.Failed), "COT-9")

        assertEquals(EmisionPhase.Rejected, viewModel.state.value.phase)
        assertNull(viewModel.state.value.cotizacionId)
    }

    private fun scripted(answer: StandInAnswer<AcceptedQuote>) = object : OfferRepository {
        override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> = StandInAnswer.Failed

        override suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer> = StandInAnswer.Failed

        override suspend fun accept(cotizacionId: String): StandInAnswer<AcceptedQuote> = answer
    }
}
