package com.grupo8_uniandes.solventa.claim

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.claim.DeviceRenewal
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimDetail
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimPayment
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.MemoryRenewal
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenParametricPayment
import com.grupo8_uniandes.solventa.domain.bff.push.PushDestination
import com.grupo8_uniandes.solventa.domain.bff.push.PushNotice
import com.grupo8_uniandes.solventa.domain.bff.push.PushType
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
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
class ParametricoStoredTest {
    @Before
    fun main() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun done() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenAStoredPayment_whenOpened_thenTheDetailFieldsShowAndRenewalDoesNotCharge() {
        val claims = QuietClaims(detail())
        val renewal = MemoryRenewal()
        val model = ParametricoViewModel(OpenParametricPayment(claims), claims, renewal)
        model.loadStored("internal")
        val state = model.state.value
        assertEquals("vuelo", state.notice?.asunto)
        assertEquals("90 min", state.notice?.disparo)
        assertEquals(180000L, state.notice?.monto)
        assertEquals("COP", state.notice?.moneda)
        assertEquals("POL-1", state.poliza)
        model.setRenewal(true)
        assertTrue(renewal.read("POL-1"))
        model.setRenewal(false)
        assertFalse(renewal.read("POL-1"))
        assertEquals(0, claims.charges)
        val context = ApplicationProvider.getApplicationContext<Context>()
        val device = DeviceRenewal(context)
        device.write("POL-9", true)
        assertTrue(device.read("POL-9"))
    }

    @Test
    fun givenAFailedDetail_whenOpened_thenRetryCanLoadIt() {
        val claims = QuietClaims(null)
        val model = ParametricoViewModel(OpenParametricPayment(claims), claims, MemoryRenewal())
        model.loadStored("internal")
        assertTrue(model.state.value.failed)
        claims.detail = detail()
        model.loadStored("internal")
        assertEquals("POL-1", model.state.value.poliza)
    }

    @Test
    fun givenNoNotice_whenOpened_thenRenewalAndTheReceiptStayIdle() {
        val claims = object : ClaimRepository {
            override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?) = StandInAnswer.Failed
            override suspend fun list() = StandInAnswer.Failed
            override suspend fun detail(id: String) = StandInAnswer.Rejected("ausente")
        }
        val model = ParametricoViewModel(OpenParametricPayment(claims), claims)
        assertNull(model.offerReceipt())
        model.setRenewal(true)
        assertFalse(model.state.value.renewalChecked)
        model.loadStored("ausente")
        assertTrue(model.state.value.missing)
        model.load("ausente")
        assertTrue(model.state.value.failed)
        model.openPush(
            PushNotice(PushType.VENCIMIENTO, "otro", "cuerpo", PushDestination.AVISO_VENCIMIENTO, "POL-1"),
        )
        assertNull(model.state.value.notice)
        ParametricoViewModel(OpenParametricPayment(claims), null).loadStored("ausente")
    }

    @Test
    fun givenTheStoredClaim_whenLoaded_thenRenewalReadsThePolicy() {
        val renewal = MemoryRenewal()
        renewal.write(OpenParametricPayment.POLICY, true)
        val claims = object : ClaimRepository {
            override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?) = StandInAnswer.Failed
            override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Ready(
                listOf(
                    ClaimSummary(
                        OpenParametricPayment.STORED_ID,
                        "Clima",
                        "vuelo",
                        ClaimStatus.PAGADO,
                        estadoTexto = OpenParametricPayment.STORED_STATUS,
                    ),
                ),
            )
            override suspend fun detail(id: String) = StandInAnswer.Ready(
                detail().copy(poliza = null, summary = detail().summary.copy(tipo = "asistido", estado = ClaimStatus.RECIBIDO)),
            )
        }
        val model = ParametricoViewModel(OpenParametricPayment(claims), claims, renewal)
        model.load(OpenParametricPayment.STORED_ID)
        assertEquals(OpenParametricPayment.SUBJECT, model.state.value.notice?.asunto)
        assertTrue(model.state.value.renewalChecked)
        model.loadStored("internal")
        assertTrue(model.state.value.failed)
        assertNull(model.state.value.poliza)
    }

    private fun detail() = ClaimDetail(
        summary = ClaimSummary("SIN-9", "Clima", "vuelo", ClaimStatus.PAGADO, tipo = "parametrico"),
        poliza = "POL-1",
        descripcion = "Retraso",
        lugar = null,
        geo = null,
        motivo = null,
        evidencia = emptyList(),
        historial = emptyList(),
        pago = ClaimPayment("C-1", 180000.0, "COP", "2026-11-01"),
        umbral = "90 min",
    )

    private class QuietClaims(var detail: ClaimDetail?) : ClaimRepository {
        var charges = 0
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> {
            charges += 1
            return StandInAnswer.Failed
        }

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Ready(emptyList())

        override suspend fun detail(id: String): StandInAnswer<ClaimDetail> =
            detail?.let { StandInAnswer.Ready(it) } ?: StandInAnswer.Failed
    }
}
