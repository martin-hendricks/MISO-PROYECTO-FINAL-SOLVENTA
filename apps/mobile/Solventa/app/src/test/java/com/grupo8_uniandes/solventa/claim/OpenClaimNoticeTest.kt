package com.grupo8_uniandes.solventa.claim

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.bff.remote.BffCache
import com.grupo8_uniandes.solventa.data.bff.remote.CachedClaimHold
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.EvidenceBytes
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
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

        assertEquals("", notice.review().poliza)
        assertEquals("", notice.review().fechaHecho)
        assertEquals("", notice.review().descripcion)
        assertEquals("", notice.review().lugar)
        assertEquals(
            listOf(
                "POL-88219-CO · Protección de dispositivo",
                "12 mar 2026",
                "Pantalla rota al caer el teléfono",
                "Av. Caracas con Calle 72",
            ),
            ClaimNoticeDraft.Review.displaySentences(),
        )
        assertEquals(
            listOf(
                "Los campos siguen el ramo de la póliza que elijas",
                "Escribe el lugar. Geoetiqueta solo si la activas.",
            ),
            notice.review().helpLines(),
        )
        assertEquals("2026-03-12", ClaimNoticeDraft.Review.fechaHecho)
        assertEquals(notice.review(), notice.review().copy())
        assertTrue(notice.review().adjuntos.isEmpty())
    }

    @Test
    fun givenContinue_whenEvidenceOpens_thenNoPhotoIsAttached() {
        val notice = open()
        notice.fillSample()

        notice.continueToEvidence()

        assertEquals(NoticePhase.Evidence, notice.phase)
        assertTrue(notice.draft.adjuntos.isEmpty())
    }

    @Test
    fun givenAPhoto_whenTheNoticeIsSent_thenSin441ArrivesOnce() = runBlocking {
        val repo = RecordingClaims()
        val notice = open(repo)

        notice.attachFile(file(AttachmentKind.FOTO, "foto.jpg", "image/jpeg"), byteArrayOf(1, 2))
        val first = notice.send()
        val second = notice.send()

        assertEquals(listOf(AttachmentKind.FOTO), repo.notice?.adjuntos?.map { it.tipo })
        assertEquals("foto.jpg", repo.notice?.adjuntos?.single()?.nombre)
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
    fun givenEvidence_whenPhotoVideoAndReceiptAreAttached_thenTheyStayOnTheNotice() = runBlocking {
        val repo = RecordingClaims()
        val notice = open(repo)
        notice.attachFile(file(AttachmentKind.FOTO, "foto.jpg", "image/jpeg"), byteArrayOf(1))
        notice.attachFile(file(AttachmentKind.VIDEO, "video.mp4", "video/mp4"), byteArrayOf(2))
        notice.attachFile(file(AttachmentKind.RECIBO, "recibo.pdf", "application/pdf"), byteArrayOf(3))
        notice.attachFile(file(AttachmentKind.SOPORTE, "soporte.png", "image/png"), byteArrayOf(4))

        notice.send()

        assertEquals(
            listOf(AttachmentKind.FOTO, AttachmentKind.VIDEO, AttachmentKind.RECIBO, AttachmentKind.SOPORTE),
            repo.notice?.adjuntos?.map { it.tipo },
        )
        assertEquals(
            listOf("foto.jpg", "video.mp4", "recibo.pdf", "soporte.png"),
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
        notice.fillSample()
        notice.continueToEvidence()
        notice.attachFile(file(AttachmentKind.FOTO, "foto.jpg", "image/jpeg"), byteArrayOf(1))

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
        notice.attachFile(file(AttachmentKind.FOTO, "foto.jpg", "image/jpeg"), byteArrayOf(1))
        notice.setGeotag(true)
        notice.placeAt(null)

        notice.send()

        assertNull(repo.notice?.geo)
        assertTrue(notice.draft.locationDenied)
        assertEquals("SIN-441", notice.receipt?.siniestroId)
    }

    @Test
    fun givenGeotagIsOn_whenAPointIsPlaced_thenTheCoordinateStaysUntilItIsTurnedOff() {
        val notice = open()
        notice.setGeotag(true)
        notice.placeAt(GeoPoint(lat = 4.6533, lng = -74.0836, precisionM = 12))

        assertEquals(NoticePhase.Form, notice.phase)
        assertTrue(notice.draft.geotag)
        assertEquals(4.6533, notice.draft.geo!!.lat, 0.0001)
        assertEquals(-74.0836, notice.draft.geo!!.lng, 0.0001)
        assertEquals(12, notice.draft.geo?.precisionM)

        notice.setGeotag(false)
        assertNull(notice.draft.geo)
        assertFalse(notice.draft.geotag)
    }

    @Test
    fun givenAFile_whenItIsRemoved_thenTheBytesGoWithIt() {
        val notice = open()
        notice.attachFile(file(AttachmentKind.FOTO, "foto.jpg", "image/jpeg"), byteArrayOf(9))
        notice.markCameraDenied()
        notice.remove("foto.jpg")

        assertTrue(notice.draft.adjuntos.isEmpty())
        assertTrue(notice.draft.cameraDenied)
        assertNull(EvidenceBytes.read("foto.jpg"))
    }

    @Test
    fun givenAFreshNotice_whenDefaultsRunAndSendFails_thenNothingIsReceived() = runBlocking {
        val repo = RecordingClaims(fail = true)
        val notice = OpenClaimNotice(repo)
        val hold = MemoryClaimHold()
        hold.keep("saved", ClaimNoticeDraft.Review.toNotice())
        assertEquals(ClaimNoticeDraft.Review.toNotice(), hold.readNotice())

        notice.attachFile(file(AttachmentKind.FOTO, "foto.jpg", "image/jpeg"), byteArrayOf(1))
        notice.attachFile(file(AttachmentKind.FOTO, "foto.jpg", "image/jpeg"), byteArrayOf(1))
        assertNull(notice.send())
        assertEquals(NoticePhase.Form, notice.phase)
        assertTrue(notice.queue().isNotEmpty())
    }

    private fun file(kind: AttachmentKind, name: String, type: String) =
        Attachment(kind, name, type, 4)

    private fun open(repo: ClaimRepository = RecordingClaims()) =
        OpenClaimNotice(repo, MemoryClaimHold()) { "key-1" }

    private fun OpenClaimNotice.fillSample() {
        val sample = ClaimNoticeDraft.Review
        revise(sample.poliza, sample.fechaHecho, sample.descripcion, sample.lugar)
    }

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
