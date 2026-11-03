package com.grupo8_uniandes.solventa.claim

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.bff.remote.BffCache
import com.grupo8_uniandes.solventa.data.bff.remote.CachedClaimHold
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNoticeDraft
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.MemoryClaimHold
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class OpenClaimNoticeTest {
    @Test
    fun givenTheReviewNotice_whenItIsShown_thenTheFrameCopyAndDateAreReady() {
        val notice = open()

        assertEquals(
            listOf(
                "POL-88219-CO · Protección de dispositivo",
                "12 mar 2026",
                "Pantalla rota al caer el teléfono",
                "Av. Caracas con Calle 72",
            ),
            notice.review().displaySentences(),
        )
        assertEquals(
            listOf(
                "Los campos siguen el ramo de la póliza que elijas",
                "Pide permiso de ubicacion del dispositivo para geoetiquetar",
            ),
            notice.review().helpLines(),
        )
        assertEquals("2026-03-12", notice.review().fechaHecho)
        assertEquals(notice.review(), notice.review().copy())
        assertTrue(notice.review().adjuntos.isEmpty())
    }

    @Test
    fun givenContinue_whenTheCameraIsNotAnswered_thenNoPhotoIsAttached() {
        val notice = open()

        notice.continueToCamera()

        assertEquals(NoticePhase.Camera, notice.phase)
        assertTrue(notice.draft.adjuntos.isEmpty())
    }

    @Test
    fun givenTheCameraIsAllowed_whenTheNoticeIsSent_thenSin441ArrivesOnce() = runBlocking {
        val repo = RecordingClaims()
        val notice = open(repo)

        notice.allowCamera()
        val first = notice.send()
        val second = notice.send()

        assertEquals(listOf(AttachmentKind.FOTO), repo.notice?.adjuntos?.map { it.tipo })
        assertEquals("foto-dano", repo.notice?.adjuntos?.single()?.nombre)
        assertEquals("SIN-441", first?.siniestroId)
        assertEquals(ClaimStatus.EN_EVALUACION, first?.estado)
        assertEquals(first, second)
        assertEquals(1, repo.calls)
        assertFalse(notice.sendOffered())
        assertEquals(NoticePhase.Confirmation, notice.phase)
    }

    @Test
    fun givenTheForm_whenTheCustomerCancels_thenThereIsNoReceipt() = runBlocking {
        val repo = RecordingClaims()
        val notice = open(repo)

        notice.cancel()

        assertEquals(0, repo.calls)
        assertNull(notice.receipt)
        assertEquals(NoticePhase.Closed, notice.phase)
    }

    @Test
    fun givenThePhotoStep_whenVideoReceiptAndScanAreAttached_thenTheyStayOnTheNotice() = runBlocking {
        val repo = RecordingClaims()
        val notice = open(repo)
        notice.allowCamera()
        notice.attachVideo()
        notice.attachReceipt()
        notice.attachSupport()

        notice.send()

        assertEquals(
            listOf(AttachmentKind.FOTO, AttachmentKind.VIDEO, AttachmentKind.RECIBO, AttachmentKind.SOPORTE),
            repo.notice?.adjuntos?.map { it.tipo },
        )
        assertEquals(
            listOf("foto-dano", "video-dano", "recibo-dano", "soporte-recorte"),
            repo.notice?.adjuntos?.map { it.nombre },
        )
    }

    @Test
    fun givenGuardarEnCola_whenChosen_thenThereIsNoReceiptAndOneKey() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val cache = BffCache(context).also { it.clear() }
        val hold = CachedClaimHold(cache)
        val repo = RecordingClaims()
        val notice = OpenClaimNotice(repo, hold) { "key-held" }
        notice.allowCamera()

        val first = notice.queue()
        val second = notice.queue()

        assertEquals("key-held", first)
        assertEquals(first, second)
        assertEquals("key-held", cache.readClaim()?.key)
        assertNull(notice.receipt)
        assertEquals(0, repo.calls)
        assertEquals(NoticePhase.Evidence, notice.phase)

        val sent = notice.send()

        assertEquals("key-held", repo.key)
        assertEquals(1, repo.calls)
        assertEquals("SIN-441", sent?.siniestroId)
        assertNull(cache.readClaim())
    }

    @Test
    fun givenLocationIsDenied_whenTheNoticeIsSent_thenGeoIsNull() = runBlocking {
        val repo = RecordingClaims()
        val notice = open(repo)
        notice.allowCamera()
        notice.denyLocation()

        notice.send()

        assertNull(repo.notice?.geo)
        assertTrue(notice.draft.locationDenied)
        assertEquals("SIN-441", notice.receipt?.siniestroId)
    }

    @Test
    fun givenLocationIsAllowed_whenTheEvidenceIsShown_thenTheCoordinateIsSet() {
        val notice = open()
        notice.allowLocation()

        assertEquals(NoticePhase.Evidence, notice.phase)
        assertEquals(4.6533, notice.draft.geo!!.lat, 0.0001)
        assertEquals(-74.0836, notice.draft.geo!!.lng, 0.0001)
        assertEquals(12, notice.draft.geo?.precisionM)
    }

    @Test
    fun givenTheCameraIsDenied_whenAGalleryPhotoIsAllowed_thenOnePhotoStaysAndTheNoticeIsOpen() {
        val notice = open()
        notice.denyCamera()
        notice.choosePhotos()
        notice.allowPhotos()

        assertEquals(listOf(AttachmentKind.FOTO), notice.draft.adjuntos.map { it.tipo })
        assertEquals("foto-dano", notice.draft.adjuntos.single().nombre)
        assertEquals(NoticePhase.Evidence, notice.phase)
        assertNull(notice.receipt)
    }

    @Test
    fun givenAFreshNotice_whenDefaultsRunAndSendFails_thenNothingIsReceived() = runBlocking {
        val repo = RecordingClaims(fail = true)
        val notice = OpenClaimNotice(repo)
        val hold = MemoryClaimHold()
        hold.keep("saved", ClaimNoticeDraft.Review.toNotice())
        assertEquals(ClaimNoticeDraft.Review.toNotice(), hold.readNotice())

        notice.allowCamera()
        notice.allowCamera()
        assertNull(notice.send())
        assertEquals(NoticePhase.Evidence, notice.phase)
        assertTrue(notice.queue().isNotEmpty())
    }

    private fun open(repo: ClaimRepository = RecordingClaims()) =
        OpenClaimNotice(repo, MemoryClaimHold()) { "key-1" }

    private class RecordingClaims(private val fail: Boolean = false) : ClaimRepository {
        var notice: ClaimNotice? = null
        var key: String? = null
        var calls = 0

        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> {
            this.notice = notice
            key = idempotencyKey
            calls += 1
            if (fail) return StandInAnswer.Failed
            return StandInAnswer.Ready(ClaimReceipt("SIN-441", ClaimStatus.EN_EVALUACION))
        }

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Failed
    }
}
