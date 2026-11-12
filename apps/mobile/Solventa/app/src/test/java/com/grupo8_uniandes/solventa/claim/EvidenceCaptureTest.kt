package com.grupo8_uniandes.solventa.claim

import android.content.Context
import android.provider.MediaStore
import android.location.Location
import android.location.LocationManager
import android.net.Uri
import android.provider.OpenableColumns
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.claim.PlatformLocator
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimPayment
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimDetail
import com.grupo8_uniandes.solventa.domain.bff.claim.EvidenceBytes
import com.grupo8_uniandes.solventa.domain.bff.claim.bytesMissing
import com.grupo8_uniandes.solventa.domain.bff.claim.storedFiles
import com.grupo8_uniandes.solventa.ui.capture.LimitedCaptureVideo
import com.grupo8_uniandes.solventa.ui.capture.evidenceKind
import com.grupo8_uniandes.solventa.ui.capture.evidenceMime
import com.grupo8_uniandes.solventa.ui.capture.readFile
import com.grupo8_uniandes.solventa.ui.capture.readPicked
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.fakes.RoboCursor
import java.io.ByteArrayInputStream
import java.io.File

@RunWith(RobolectricTestRunner::class)
class EvidenceCaptureTest {
    @Test
    fun givenAContentJpeg_whenRead_thenTheAttachmentKeepsNameTypeAndBytes() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val uri = Uri.parse("content://solventa/dano.jpg")
        val bytes = byteArrayOf(1, 2, 3, 4)
        val cursor = RoboCursor().apply {
            setColumnNames(listOf(OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE))
            setResults(arrayOf(arrayOf<Any>("dano.jpg", 4L)))
        }
        shadowOf(context.contentResolver).setCursor(uri, cursor)
        shadowOf(context.contentResolver).registerInputStream(uri, ByteArrayInputStream(bytes))

        val picked = readPicked(context.contentResolver, uri)

        assertEquals("dano.jpg", picked!!.attachment.nombre)
        assertEquals(AttachmentKind.FOTO, picked.attachment.tipo)
        assertEquals("image/jpeg", picked.attachment.contentType)
        assertEquals(4L, picked.attachment.tamanoBytes)
        assertEquals(4, picked.bytes.size)
    }

    @Test
    fun givenAnEmptyStream_whenRead_thenNothingIsReturned() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val uri = Uri.parse("content://solventa/vacio.jpg")
        shadowOf(context.contentResolver).registerInputStream(uri, ByteArrayInputStream(byteArrayOf()))
        assertNull(readPicked(context.contentResolver, uri))
    }

    @Test
    fun givenACacheFile_whenRead_thenTheExtensionChoosesTheKind() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val file = File(context.cacheDir, "claim/clip.mp4")
        file.parentFile?.mkdirs()
        file.writeBytes(byteArrayOf(9, 8, 7))

        val picked = readPicked(context.contentResolver, Uri.fromFile(file))

        assertEquals("clip.mp4", picked!!.attachment.nombre)
        assertEquals(AttachmentKind.VIDEO, picked.attachment.tipo)
        assertEquals("video/mp4", picked.attachment.contentType)
    }

    @Test
    fun givenACacheFile_whenReadDirectly_thenAnEmptyFileIsIgnored() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val empty = File(context.cacheDir, "claim/vacio.jpg")
        empty.parentFile?.mkdirs()
        empty.writeBytes(byteArrayOf())
        assertNull(readFile(empty))
        val photo = File(context.cacheDir, "claim/foto.jpg")
        photo.writeBytes(byteArrayOf(1, 2))
        val picked = readFile(photo)
        assertEquals(AttachmentKind.FOTO, picked!!.attachment.tipo)
        assertEquals("image/jpeg", picked.attachment.contentType)
        val unknown = File(context.cacheDir, "claim/nota.txt")
        unknown.writeBytes(byteArrayOf(3))
        assertEquals(AttachmentKind.SOPORTE, readFile(unknown)!!.attachment.tipo)
    }

    @Test
    fun givenAVideoUri_whenTheContractBuildsTheIntent_thenItCapsDurationAndSize() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val intent = LimitedCaptureVideo().createIntent(context, Uri.parse("content://solventa/v.mp4"))
        assertEquals(30, intent.getIntExtra(MediaStore.EXTRA_DURATION_LIMIT, 0))
        assertEquals(10L * 1024 * 1024, intent.getLongExtra(MediaStore.EXTRA_SIZE_LIMIT, 0))
    }

    @Test
    fun givenMimeNames_whenMapped_thenJpegPdfAndUnknownStayDistinct() {
        assertEquals("image/jpeg", evidenceMime("image/jpg", "a.jpg"))
        assertEquals("application/pdf", evidenceMime("application/pdf", "a.pdf"))
        assertEquals(AttachmentKind.RECIBO, evidenceKind("application/pdf"))
        assertEquals(null, evidenceKind("application/zip"))
        assertEquals("application/octet-stream", evidenceMime(null, "sin-extension"))
    }

    @Test
    fun givenGpsThenNetwork_whenRead_thenTheFirstFixWins() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val manager = context.getSystemService(LocationManager::class.java)
        val shadow = shadowOf(manager)
        shadow.setProviderEnabled(LocationManager.GPS_PROVIDER, true)
        shadow.setProviderEnabled(LocationManager.NETWORK_PROVIDER, true)
        shadow.setLastKnownLocation(LocationManager.GPS_PROVIDER, point(LocationManager.GPS_PROVIDER, 4.65, -74.08, 12f))
        shadow.setLastKnownLocation(LocationManager.NETWORK_PROVIDER, point(LocationManager.NETWORK_PROVIDER, 1.0, 2.0, 40f))

        val located = PlatformLocator(context, timeoutMs = 50).current()

        assertEquals(4.65, located!!.lat, 0.001)
        assertEquals(-74.08, located.lng, 0.001)
        assertEquals(12, located.precisionM)
    }

    @Test
    fun givenOnlyNetwork_whenRead_thenThatFixIsUsed() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val manager = context.getSystemService(LocationManager::class.java)
        val shadow = shadowOf(manager)
        shadow.setProviderEnabled(LocationManager.GPS_PROVIDER, false)
        shadow.setProviderEnabled(LocationManager.NETWORK_PROVIDER, true)
        shadow.setLastKnownLocation(
            LocationManager.NETWORK_PROVIDER,
            Location(LocationManager.NETWORK_PROVIDER).apply {
                latitude = 6.2
                longitude = -75.5
                time = System.currentTimeMillis()
            },
        )

        val located = PlatformLocator(context, timeoutMs = 50).current()

        assertEquals(6.2, located!!.lat, 0.001)
        assertEquals(0, located.precisionM)
    }

    @Test
    fun givenNoProvider_whenRead_thenThereIsNoPoint() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val manager = context.getSystemService(LocationManager::class.java)
        val shadow = shadowOf(manager)
        shadow.setProviderEnabled(LocationManager.GPS_PROVIDER, false)
        shadow.setProviderEnabled(LocationManager.NETWORK_PROVIDER, false)

        assertNull(PlatformLocator(context, timeoutMs = 50).current())
    }

    @Test
    fun givenAJpegAliasAndAnEmptyFile_whenRead_thenTheMimeIsNormalizedAndTheFileIsSkipped() {
        assertEquals("image/jpeg", evidenceMime("image/jpg", "a.jpg"))
        assertEquals("image/jpeg", evidenceMime("image/pjpeg", "a.jpg"))
        assertEquals("video/mp4", evidenceMime("video/mp4", "a.mp4"))
        assertEquals(com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind.VIDEO, evidenceKind("video/mp4"))
        assertNull(evidenceKind("text/plain"))
        val empty = File.createTempFile("vacio", ".bin")
        empty.writeBytes(ByteArray(0))
        assertNull(readFile(empty))
        val note = File.createTempFile("nota", ".txt")
        note.writeBytes(byteArrayOf(1))
        assertEquals(1, readFile(note)!!.bytes.size)
    }

    @Test
    fun givenStoredBytes_whenANoticeAsks_thenMissingAndPresentFilesAreBothRead() {
        EvidenceBytes.clear()
        EvidenceBytes.keep("foto.jpg", byteArrayOf(1, 2))
        val notice = ClaimNotice(
            poliza = "POL-1",
            fechaHecho = "2026-11-01",
            geo = null,
            adjuntos = listOf(
                Attachment(AttachmentKind.FOTO, "foto.jpg", tamanoBytes = 2),
                Attachment(AttachmentKind.SOPORTE, "acta.pdf", tamanoBytes = 4),
                Attachment(AttachmentKind.RECIBO, "vacio.pdf", tamanoBytes = 0),
            ),
        )
        assertTrue(notice.bytesMissing())
        val stored = notice.storedFiles()
        assertEquals(3, stored.size)
        assertEquals(2, stored[0].size)
        assertEquals(0, stored[1].size)
        EvidenceBytes.drop("foto.jpg")
        assertNull(EvidenceBytes.read("foto.jpg"))
    }

    @Test
    fun givenAPaymentThatIsNotParametric_whenStored_thenThereIsNoNotice() {
        val detail = ClaimDetail(
            summary = ClaimSummary("SIN-1", "SOAT", "Choque", ClaimStatus.PAGADO, tipo = "asistido"),
            poliza = null,
            descripcion = null,
            lugar = null,
            geo = null,
            motivo = null,
            evidencia = emptyList(),
            historial = emptyList(),
            pago = ClaimPayment("CMP", 1.0, "COP", "2026-11-01"),
            umbral = null,
        )
        assertNull(detail.storedPayment())
        assertNull(detail.copy(pago = null).storedPayment())
        assertFalse(
            detail.copy(
                summary = detail.summary.copy(tipo = "parametrico", estado = ClaimStatus.RECIBIDO),
            ).storedPayment() != null,
        )
    }

    private fun point(provider: String, lat: Double, lng: Double, accuracy: Float) =
        Location(provider).apply {
            latitude = lat
            longitude = lng
            this.accuracy = accuracy
            time = System.currentTimeMillis()
        }
}
