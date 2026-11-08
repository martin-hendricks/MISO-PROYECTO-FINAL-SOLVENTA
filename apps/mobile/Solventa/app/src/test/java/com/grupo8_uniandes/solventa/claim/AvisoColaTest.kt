package com.grupo8_uniandes.solventa.claim

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.claim.ClaimReplay
import com.grupo8_uniandes.solventa.data.claim.EncryptedNoticeStore
import com.grupo8_uniandes.solventa.data.claim.KeptNotice
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
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class AvisoColaTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()

    @Test
    fun givenAKeptNotice_whenItIsStored_thenTheKeyFilesAndNoticeRoundTrip() {
        val store = store()
        val notice = notice()
        val bytes = byteArrayOf(1, 2, 3)
        store.save(KeptNotice("key-11111111", notice, listOf(bytes)))
        val kept = store.read()
        assertEquals("key-11111111", kept?.key)
        assertEquals("POL-1", kept?.notice?.poliza)
        assertTrue(bytes.contentEquals(kept!!.files.single()))
        val withGeo = notice.copy(geo = com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint(4.6, -74.0, 8))
        store.save(KeptNotice("key-22222222", withGeo, listOf(bytes)))
        assertEquals(4.6, store.read()?.notice?.geo?.lat)
        store.clear()
        assertNull(store.read())
    }

    @Test
    fun givenANetworkFailure_whenReplayedTwice_thenOneClaimIsCreated() = runBlocking {
        val store = store()
        val repo = OnceClaims()
        val notice = notice()
        store.save(KeptNotice("key-11111111", notice, listOf(byteArrayOf(9))))
        val replay = ClaimReplay(store, repo)
        assertEquals("SIN-1", replay.replay()?.siniestroId)
        assertNull(replay.replay())
        assertEquals(1, repo.calls)
        assertEquals(listOf("key-11111111"), repo.keys)
    }

    @Test
    fun givenMissingBytes_whenReplayed_thenNothingIsSent() = runBlocking {
        val store = store()
        val repo = OnceClaims()
        store.save(KeptNotice("key-11111111", notice(), listOf(byteArrayOf())))
        assertNull(ClaimReplay(store, repo).replay())
        assertEquals(0, repo.calls)
        assertEquals("key-11111111", store.read()?.key)
    }

    @Test
    fun givenAFailedReplay_whenTheHostStillFails_thenTheNoticeStays() = runBlocking {
        val store = store()
        val repo = FailThenReady()
        store.save(KeptNotice("key-11111111", notice(), listOf(byteArrayOf(9))))
        assertNull(ClaimReplay(store, repo).replay())
        assertEquals("key-11111111", store.read()?.key)
    }

    @Test
    fun givenQueueOrAFailedSend_whenTheArchiveIsUsed_thenTheSameKeyIsKept() = runBlocking {
        val store = store()
        val repo = FailThenReady()
        val notice = OpenClaimNotice(repo, MemoryClaimHold(), store) { "key-11111111" }
        notice.attachFile(Attachment(AttachmentKind.FOTO, "a.png", "image/png", 4), byteArrayOf(1, 2, 3, 4))
        notice.queue()
        assertEquals("key-11111111", store.read()?.key)
        assertEquals(4, store.read()?.files?.single()?.size)
        assertNull(notice.send())
        repo.fail = false
        assertEquals("SIN-1", ClaimReplay(store, repo).replay()?.siniestroId)
    }

    private fun store() = EncryptedNoticeStore(context, "solventa-clave-1").also { it.clear() }

    private fun notice() = ClaimNotice(
        poliza = "POL-1",
        fechaHecho = "2026-11-01",
        geo = null,
        adjuntos = listOf(Attachment(AttachmentKind.FOTO, "a.png", "image/png", 3)),
        descripcion = "Choque",
        lugar = "Calle 72",
    )

    private class OnceClaims : ClaimRepository {
        var calls = 0
        val keys = mutableListOf<String?>()
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> {
            calls += 1
            keys += idempotencyKey
            return StandInAnswer.Ready(ClaimReceipt("SIN-1", ClaimStatus.RECIBIDO))
        }

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Ready(emptyList())
    }

    private class FailThenReady : ClaimRepository {
        var fail = true
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> =
            if (fail) StandInAnswer.Failed else StandInAnswer.Ready(ClaimReceipt("SIN-1", ClaimStatus.RECIBIDO))

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Ready(emptyList())
    }
}
