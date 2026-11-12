package com.grupo8_uniandes.solventa.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate

class AvisoFormTest {
    private val today = LocalDate.of(2026, 11, 6)

    @Test
    fun givenTwoPolicies_whenOffered_thenOnlyThoseNumbersStaySelectable() {
        val notice = open()
        notice.offerPolicies(listOf("POL-1", "POL-2"))
        assertEquals("", notice.draft.poliza)
        notice.revise(poliza = "POL-9", fechaHecho = "2026-11-01", descripcion = "Choque", lugar = "")
        notice.continueToEvidence()
        assertEquals(NoticePhase.Form, notice.phase)
        assertTrue(notice.problems().policy)
        assertEquals("POL-9", notice.draft.poliza)
    }

    @Test
    fun givenOnePolicy_whenOffered_thenItIsPreselected() {
        val notice = open()
        notice.offerPolicies(listOf("POL-1"))
        assertEquals("POL-1", notice.draft.poliza)
    }

    @Test
    fun givenNoPolicy_whenTheFormOpens_thenItExplainsAndDoesNotContinue() {
        val notice = open()
        notice.revise(poliza = "", fechaHecho = "2026-11-01", descripcion = "Choque", lugar = "")
        notice.continueToEvidence()
        assertTrue(notice.problems().noPolicy)
        assertEquals(NoticePhase.Form, notice.phase)
    }

    @Test
    fun givenAFutureDateOrBlankDescription_whenContinuing_thenTheStepStaysAndValuesRemain() {
        val notice = open()
        notice.revise(poliza = "POL-1", fechaHecho = "2026-11-07", descripcion = "   ", lugar = "Calle 72")
        notice.continueToEvidence()
        assertTrue(notice.problems().date)
        assertTrue(notice.problems().description)
        assertEquals("2026-11-07", notice.draft.fechaHecho)
        assertEquals("   ", notice.draft.descripcion)
        assertEquals(NoticePhase.Form, notice.phase)
    }

    @Test
    fun givenAPlaceOver200_whenContinuing_thenThePlaceIsMarked() {
        val notice = open()
        notice.revise(poliza = "POL-1", fechaHecho = "2026-11-01", descripcion = "Choque", lugar = "x".repeat(201))
        notice.continueToEvidence()
        assertTrue(notice.problems().place)
        assertFalse(notice.problems().canContinue)
    }

    @Test
    fun givenAValidForm_whenContinuing_thenEvidenceCanOpen() {
        val notice = open()
        notice.revise(poliza = "POL-1", fechaHecho = "2026-11-01", descripcion = "Choque", lugar = "")
        notice.continueToEvidence()
        assertEquals(NoticePhase.Evidence, notice.phase)
        assertTrue(notice.attempted)
        notice.revise()
        assertEquals("POL-1", notice.draft.poliza)
    }

    private fun open() = OpenClaimNotice(QuietClaims(), newKey = { "key-1" }, today = { today })

    private class QuietClaims : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?) =
            StandInAnswer.Ready(ClaimReceipt("SIN-1", com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus.RECIBIDO))

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Failed
    }
}
