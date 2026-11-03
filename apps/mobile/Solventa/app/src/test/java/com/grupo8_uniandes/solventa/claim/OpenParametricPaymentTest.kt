package com.grupo8_uniandes.solventa.claim

import com.grupo8_uniandes.solventa.data.bff.dto.PushNoticeDto
import com.grupo8_uniandes.solventa.data.bff.fixture.PublishedSamples
import com.grupo8_uniandes.solventa.data.bff.mapping.decode
import com.grupo8_uniandes.solventa.data.bff.mapping.toNotice
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenParametricPayment
import com.grupo8_uniandes.solventa.domain.bff.push.PushDestination
import com.grupo8_uniandes.solventa.domain.bff.push.PushNotice
import com.grupo8_uniandes.solventa.domain.bff.push.PushType
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class OpenParametricPaymentTest {
    private val payments = OpenParametricPayment(StoredClaims())

    @Before
    fun main() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun reset() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenTheStoredPayment_whenTheSummaryOpens_thenTheReviewNoticeHasNoThirdPartyMessage() = runBlocking {
        val notice = payments.open(OpenParametricPayment.STORED_ID)

        assertNotNull(notice)
        assertEquals("Clima y vuelos · vuelo AV-234", notice!!.asunto)
        assertEquals("Retraso > 90 min · dato oficial del vuelo", notice.disparo)
        assertEquals(180_000L, notice.monto)
        assertEquals("COP", notice.moneda)
        assertEquals("$180.000 COP depositados", notice.lineaDepositada)
        assertEquals(OpenParametricPayment.review, notice)
        assertFalse(notice.asunto.contains("tercero"))
        assertFalse(notice.disparo.contains("tercero"))
        assertFalse(notice.lineaDepositada.contains("tercero"))
    }

    @Test
    fun givenAnotherClaim_whenItIsOpened_thenThisNoticeIsNotReturned() = runBlocking {
        assertNull(payments.open("SIN-441"))
        assertNull(OpenParametricPayment(FailedClaims()).open("SIN-P01"))
        assertNull(
            OpenParametricPayment(
                StoredClaims(
                    ClaimSummary(
                        siniestroId = "SIN-P01",
                        ramo = "Clima y vuelos",
                        resumen = "retraso de vuelo",
                        estado = ClaimStatus.PAGADO,
                        estadoTexto = "Pagado",
                    ),
                ),
            ).open("SIN-P01"),
        )
        assertNull(
            OpenParametricPayment(
                StoredClaims(
                    ClaimSummary(
                        siniestroId = "SIN-P01",
                        ramo = "Clima y vuelos",
                        resumen = "retraso de vuelo",
                        estado = ClaimStatus.EN_EVALUACION,
                        estadoTexto = "Pago automático · pagado",
                    ),
                ),
            ).open("SIN-P01"),
        )
    }

    @Test
    fun givenAParametricPush_whenItIsOpened_thenItIsTheSameNotice() = runBlocking {
        val push = decode<PushNoticeDto>(PublishedSamples.PARAMETRIC_PUSH)!!.toNotice()
        val fromPush = payments.open(push)
        val fromList = payments.open(OpenParametricPayment.STORED_ID)

        assertEquals(PushType.PAGO_AUTOMATICO, push.tipo)
        assertEquals(PushDestination.PARAMETRICO, push.destino)
        assertEquals(fromList, fromPush)
        assertEquals(push, OpenParametricPayment.reviewPush())
        assertNull(payments.open(push.copy(destino = PushDestination.DETALLE_SINIESTRO)))
        assertNull(payments.open(push.copy(titulo = "Otro aviso")))
        assertNull(payments.open(push.copy(cuerpo = "mensaje del tercero")))
        assertFalse(push.cuerpo.contains("tercero"))
        assertFalse(push.titulo.contains("tercero"))
    }

    @Test
    fun givenThePublishedExpiryNotice_whenItIsRead_thenTheSummaryStays() = runBlocking {
        val published = decode<PushNoticeDto>(PublishedSamples.PUSH_NOTICE)!!.toNotice()

        assertNull(payments.open(published))
        assertNotNull(payments.open(OpenParametricPayment.STORED_ID))
    }

    @Test
    fun givenTheSummary_whenTheReceiptIsRequested_thenItKeepsTheDepositedLine() = runBlocking {
        val notice = payments.open(OpenParametricPayment.STORED_ID)!!
        val receipt = payments.receipt(notice)
        val viewModel = ParametricoViewModel(payments)
        assertNull(viewModel.offerReceipt())
        viewModel.openPush(PushNotice(PushType.VENCIMIENTO, "Tu póliza vence", "En 7 días", PushDestination.AVISO_VENCIMIENTO, "POL-88219-CO"))
        assertNull(viewModel.state.value.notice)
        viewModel.openPush(OpenParametricPayment.reviewPush())
        assertEquals(notice, viewModel.state.value.notice)
        viewModel.load()
        val offered = viewModel.offerReceipt()
        assertEquals(offered, viewModel.state.value.receipt)

        assertEquals("Clima y vuelos · vuelo AV-234", receipt.asunto)
        assertEquals("Retraso > 90 min · dato oficial del vuelo", receipt.disparo)
        assertEquals("$180.000 COP depositados", receipt.lineaDepositada)
        assertEquals(receipt, offered)
        assertFalse(receipt.asunto.contains("tercero"))
        val listed = (StoredClaims().list() as StandInAnswer.Ready).value
        assertEquals("SIN-P01", listed.single().siniestroId)
    }

    private class StoredClaims(
        private val claim: ClaimSummary = ClaimSummary(
            siniestroId = "SIN-P01",
            ramo = "Clima y vuelos",
            resumen = "retraso de vuelo",
            estado = ClaimStatus.PAGADO,
            estadoTexto = "Pago automático · pagado",
        ),
    ) : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> =
            StandInAnswer.Failed

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Ready(listOf(claim))
    }

    private class FailedClaims : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> =
            StandInAnswer.Failed

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Failed
    }
}
