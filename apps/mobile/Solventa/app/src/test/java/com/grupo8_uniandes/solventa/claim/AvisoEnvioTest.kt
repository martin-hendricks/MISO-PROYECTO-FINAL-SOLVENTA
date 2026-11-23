package com.grupo8_uniandes.solventa.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.MemoryClaimHold
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class AvisoEnvioTest {
    @Test
    fun givenNoFile_whenSending_thenTheNoticeIsNotSent() = runBlocking {
        val repo = ScriptedClaims()
        val notice = OpenClaimNotice(repo, MemoryClaimHold()) { "key-1" }
        assertNull(notice.send())
        assertEquals(0, repo.calls)
    }

    @Test
    fun givenABadFileOrASixthFile_whenAttaching_thenItIsRefused() {
        val notice = OpenClaimNotice(ScriptedClaims(), MemoryClaimHold()) { "key-1" }
        assertFalse(notice.attachFile(Attachment(AttachmentKind.FOTO, "a.exe", "application/x-msdownload", 10)))
        assertFalse(notice.attachFile(Attachment(AttachmentKind.FOTO, "big.png", "image/png", 11L * 1024 * 1024)))
        repeat(5) { index ->
            assertTrue(notice.attachFile(Attachment(AttachmentKind.FOTO, "f$index.png", "image/png", 20)))
        }
        assertFalse(notice.attachFile(Attachment(AttachmentKind.FOTO, "f6.png", "image/png", 20)))
        assertEquals(5, notice.draft.adjuntos.size)
    }

    @Test
    fun givenABusinessRejection_whenSending_thenTheMessageShowsAndTheNextKeyIsNew() = runBlocking {
        val repo = ScriptedClaims(rejected = "fecha futura")
        val hold = MemoryClaimHold()
        val keys = ArrayDeque(listOf("key-11111111", "key-22222222"))
        val notice = OpenClaimNotice(repo, hold) { keys.removeFirst() }
        notice.attachFile(Attachment(AttachmentKind.FOTO, "a.png", "image/png", 20))
        assertNull(notice.send())
        assertEquals("fecha futura", notice.rejection)
        assertEquals("key-11111111", repo.keys.single())
        repo.rejected = null
        notice.send()
        assertEquals(listOf("key-11111111", "key-22222222"), repo.keys)
        assertEquals("SIN-9", notice.receipt?.siniestroId)
    }

    @Test
    fun givenANetworkFailure_whenSending_thenTheKeyStays() = runBlocking {
        val repo = ScriptedClaims(fail = true)
        val notice = OpenClaimNotice(repo, MemoryClaimHold()) { "key-11111111" }
        notice.attachFile(Attachment(AttachmentKind.FOTO, "a.png", "image/png", 20))
        assertNull(notice.send())
        assertNull(notice.rejection)
        repo.fail = false
        notice.send()
        assertEquals(listOf("key-11111111", "key-11111111"), repo.keys)
    }

    private class ScriptedClaims(
        var fail: Boolean = false,
        var rejected: String? = null,
    ) : ClaimRepository {
        var calls = 0
        val keys = mutableListOf<String?>()
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> {
            calls += 1
            keys += idempotencyKey
            rejected?.let { return StandInAnswer.Rejected(it) }
            if (fail) return StandInAnswer.Failed
            return StandInAnswer.Ready(ClaimReceipt("SIN-9", ClaimStatus.RECIBIDO))
        }

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Failed
    }
}
