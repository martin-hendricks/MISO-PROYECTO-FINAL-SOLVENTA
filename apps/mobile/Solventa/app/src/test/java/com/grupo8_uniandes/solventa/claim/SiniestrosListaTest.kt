package com.grupo8_uniandes.solventa.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimDetail
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimEvidence
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimHistory
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.filtered
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class SiniestrosListaTest {
    @Before
    fun main() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun done() {
        Dispatchers.resetMain()
    }
    private val rows = listOf(
        ClaimSummary("SIN-R", "SOAT", "aviso", ClaimStatus.RECIBIDO, tipo = "asistido"),
        ClaimSummary("SIN-1", "SOAT", "choque", ClaimStatus.EN_EVALUACION, tipo = "asistido"),
        ClaimSummary("SIN-D", "SOAT", "decision", ClaimStatus.DECIDIDO, tipo = "asistido"),
        ClaimSummary("SIN-E", "SOAT", "ruta", ClaimStatus.ENRUTADO, tipo = "asistido"),
        ClaimSummary("SIN-2", "SOAT", "pago", ClaimStatus.PAGADO, tipo = "asistido"),
        ClaimSummary("SIN-P", "Clima", "vuelo", ClaimStatus.PAGADO, tipo = "parametrico"),
    )

    @Test
    fun givenTheLoadedList_whenAChipIsChosen_thenOnlyThatStatusRemains() {
        assertEquals(rows.map { it.siniestroId }, rows.filtered(null).map { it.siniestroId })
        assertEquals(listOf("SIN-R"), rows.filtered(ClaimStatus.RECIBIDO).map { it.siniestroId })
        assertEquals(listOf("SIN-1"), rows.filtered(ClaimStatus.EN_EVALUACION).map { it.siniestroId })
        assertEquals(listOf("SIN-D"), rows.filtered(ClaimStatus.DECIDIDO).map { it.siniestroId })
        assertEquals(listOf("SIN-E"), rows.filtered(ClaimStatus.ENRUTADO).map { it.siniestroId })
        assertEquals(listOf("SIN-2", "SIN-P"), rows.filtered(ClaimStatus.PAGADO).map { it.siniestroId })
    }

    @Test
    fun givenAPaidParametricRow_whenOpened_thenTheViewModelMarksItParametric() {
        val model = SiniestrosViewModel(FixedClaims(rows))
        model.selectChip(ClaimStatus.PAGADO)
        assertEquals(ClaimStatus.PAGADO, model.state.value.chip)
        model.selectChip(null)
        assertEquals(null, model.state.value.chip)
        model.selectChip(ClaimStatus.PAGADO)
        model.openClaim("SIN-P")
        assertEquals(true, model.state.value.openParametric)
        model.openClaim("SIN-2")
        assertEquals(false, model.state.value.openParametric)
    }

    @Test
    fun givenADetail_whenItLoadsOrIsMissing_thenTheLinesOrTheNotFoundStateShow() {
        val detail = ClaimDetail(
            summary = rows[0].copy(fecha = "2026-11-01"),
            poliza = "POL-1",
            descripcion = "Choque",
            lugar = "Calle 72",
            geo = GeoPoint(4.6, -74.0, 12),
            motivo = null,
            evidencia = listOf(ClaimEvidence("foto.png", "foto", "image/png", "https://example.test/foto.png")),
            historial = listOf(ClaimHistory("recibido", "2026-11-01")),
            pago = null,
            umbral = null,
        )
        val ready = SiniestroDetalleViewModel(DetailClaims(StandInAnswer.Ready(detail)), "SIN-1")
        assertEquals(DetailPhase.Ready, ready.state.value.phase)
        assertEquals(4.6, ready.state.value.claim!!.geo!!.lat, 0.0)
        assertEquals("foto.png", ready.state.value.claim!!.evidencia.single().nombre)
        assertEquals(null, detail.copy(geo = null).geo)
        assertEquals("Calle 72", ready.state.value.claim!!.lugar)
        val missing = SiniestroDetalleViewModel(DetailClaims(StandInAnswer.Rejected("not_found")), "no")
        assertEquals(DetailPhase.Missing, missing.state.value.phase)
        val failed = SiniestroDetalleViewModel(DetailClaims(StandInAnswer.Failed), "no")
        failed.load()
        assertEquals(DetailPhase.Failed, failed.state.value.phase)
    }

    private class FixedClaims(private val rows: List<ClaimSummary>) : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> =
            StandInAnswer.Failed

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Ready(rows)
    }

    private class DetailClaims(private val answer: StandInAnswer<ClaimDetail>) : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> =
            StandInAnswer.Failed

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Ready(emptyList())

        override suspend fun detail(id: String): StandInAnswer<ClaimDetail> = answer
    }
}
