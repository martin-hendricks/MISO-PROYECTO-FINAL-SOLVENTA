package com.grupo8_uniandes.solventa.quote

import com.grupo8_uniandes.solventa.data.bff.remote.problemDetail
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteAttempt
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteExplained
import com.grupo8_uniandes.solventa.domain.bff.offer.RequestFirmOffer
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class QuoteSuitabilityTest {
    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenARatioRefusal_whenTheQuoteReturns_thenTheOfferDoesNotOpen() {
        val detail = "El ratio de gastos supera el porcentaje máximo vigente"
        val attempt = runBlocking {
            RequestFirmOffer(refusing(detail)).submit(deviceLine(), deviceAnswers())
        }
        val refused = attempt as QuoteAttempt.Refused
        assertEquals(detail, refused.detail)
        val viewModel = QuoteViewModel(RequestFirmOffer(refusing(detail)))
        fill(viewModel)
        viewModel.cotizar()
        assertEquals(detail, viewModel.state.value.explanation)
        assertNull(viewModel.state.value.readyId)
        assertTrue(!viewModel.state.value.failed)
    }

    @Test
    fun givenIncomeThatIsNotPositive_whenTheQuoteExplainsIt_thenTheCustomerStaysOnTheQuote() {
        val detail = "El ingreso mensual debe ser mayor que cero"
        val viewModel = QuoteViewModel(RequestFirmOffer(refusing(detail)))
        fill(viewModel)
        viewModel.cotizar()
        assertEquals(detail, viewModel.state.value.explanation)
        assertNull(viewModel.state.value.readyId)
        viewModel.onValue("2400000")
        assertNull(viewModel.state.value.explanation)
    }

    @Test
    fun givenARatioEqualToTheMaximum_whenTheQuoteIsReady_thenAnOfferOpens() {
        val viewModel = QuoteViewModel(RequestFirmOffer(ready()))
        fill(viewModel)
        viewModel.cotizar()
        assertEquals("COT-1042", viewModel.state.value.readyId)
        assertNull(viewModel.state.value.explanation)
    }

    @Test
    fun givenAProblemBody_whenRead_thenOnlyADetailIsKept() {
        assertEquals(
            "El ratio de gastos supera el porcentaje máximo vigente",
            problemDetail("""{"detail":"El ratio de gastos supera el porcentaje máximo vigente"}"""),
        )
        assertNull(problemDetail("""{"codigo":"x","mensaje":"no"}"""))
        assertNull(problemDetail(""))
    }

    private fun refusing(detail: String) = object : OfferRepository {
        override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> =
            throw QuoteExplained(detail)

        override suspend fun requote(cotizacionId: String) = StandInAnswer.Failed

        override suspend fun accept(cotizacionId: String) = StandInAnswer.Failed
    }

    private fun ready() = object : OfferRepository {
        override suspend fun quote(ramo: String, risk: LineRisk) = StandInAnswer.Ready(
            FirmOffer("COT-1042", "Protección de dispositivo", "oferta_vigente", 89000, "COP", "2026-10-01"),
        )

        override suspend fun requote(cotizacionId: String) = StandInAnswer.Failed

        override suspend fun accept(cotizacionId: String) = StandInAnswer.Failed
    }

    private fun deviceLine() = com.grupo8_uniandes.solventa.domain.bff.offer.QuoteLine.Device

    private fun deviceAnswers() = com.grupo8_uniandes.solventa.domain.bff.offer.QuoteAnswers(
        value = "2400000",
        brand = "apple",
        model = "iPhone 15",
        olderThan12Months = false,
    )

    private fun fill(viewModel: QuoteViewModel) {
        viewModel.onValue("2400000")
        viewModel.onBrand("apple")
        viewModel.onModel("iPhone 15")
        viewModel.onAge(false)
    }
}
