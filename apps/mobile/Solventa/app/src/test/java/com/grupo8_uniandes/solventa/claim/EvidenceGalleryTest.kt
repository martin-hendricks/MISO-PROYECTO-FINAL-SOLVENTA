package com.grupo8_uniandes.solventa.claim

import android.graphics.Bitmap
import android.graphics.Color
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNoticeDraft
import com.grupo8_uniandes.solventa.domain.bff.claim.EvidenceBytes
import com.grupo8_uniandes.solventa.ui.shell.EvidenciaAvisoScreen
import com.grupo8_uniandes.solventa.ui.shell.evidenceFrame
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.After
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.io.ByteArrayOutputStream
import java.io.File

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class EvidenceGalleryTest {
    @get:Rule
    val rule = createComposeRule()

    @After
    fun clearBytes() {
        EvidenceBytes.clear()
    }

    @Test
    fun givenNoFiles_whenEvidenceOpens_thenTheSlotSaysThereIsNoEvidence() {
        show(emptyList())
        rule.onNodeWithTag("claim_evidence_preview").assertIsDisplayed()
        rule.onNodeWithText("Aún no hay evidencia").assertIsDisplayed()
        rule.onNodeWithTag("claim_send").assertIsDisplayed()
    }

    @Test
    fun givenOnlyADocument_whenEvidenceOpens_thenTheSlotIsADocumentTile() {
        show(listOf(Attachment(AttachmentKind.RECIBO, "recibo.pdf", "application/pdf", 4)))
        rule.onNodeWithTag("claim_evidence_preview").assertIsDisplayed()
        rule.onNodeWithText("1 de 5").assertIsDisplayed()
    }

    @Test
    fun givenAPhoto_whenEvidenceOpens_thenTheThumbnailIsThatPhoto() {
        val jpeg = jpeg()
        EvidenceBytes.keep("dano.jpg", jpeg)
        show(
            listOf(
                Attachment(AttachmentKind.FOTO, "dano.jpg", "image/jpeg", jpeg.size.toLong()),
                Attachment(AttachmentKind.VIDEO, "dano.mp4", "video/mp4", 4),
                Attachment(AttachmentKind.RECIBO, "recibo.pdf", "application/pdf", 4),
                Attachment(AttachmentKind.SOPORTE, "nota.txt", "text/plain", 4),
            ),
        )
        rule.onNodeWithContentDescription("dano.jpg").assertIsDisplayed()
        rule.onNodeWithTag("claim_evidence_preview").assertIsDisplayed()
        rule.onNodeWithTag("claim_thumb_dano.mp4").assertIsDisplayed()
        rule.onNodeWithTag("claim_thumb_recibo.pdf").assertIsDisplayed()
        rule.onNodeWithTag("claim_thumb_nota.txt").assertIsDisplayed()
        rule.onNodeWithText("4 de 5").assertIsDisplayed()
        rule.onNodeWithText("image/jpeg", substring = true).assertIsDisplayed()
    }

    @Test
    fun givenBytes_whenAFrameIsRequested_thenOnlyARealImageDecodes() {
        val cache = ApplicationProvider.getApplicationContext<android.content.Context>().cacheDir
        assertNotNull(evidenceFrame(jpeg(), "image/jpeg", cache))
        assertNotNull(evidenceFrame(jpeg(width = 800, height = 10), "image/jpeg", cache))
        evidenceFrame(byteArrayOf(1, 2, 3, 4), "image/jpeg", cache)
        evidenceFrame(byteArrayOf(1, 2, 3, 4), "video/mp4", cache)
        val blocked = File(cache, "not-a-directory")
        blocked.writeBytes(byteArrayOf(1))
        assertNull(evidenceFrame(byteArrayOf(1, 2, 3, 4), "video/mp4", blocked))
        assertNull(evidenceFrame(byteArrayOf(1, 2, 3, 4), "application/pdf", cache))
        assertNull(evidenceFrame(null, "image/jpeg", cache))
        assertNull(evidenceFrame(byteArrayOf(), "image/jpeg", cache))
    }

    private fun show(files: List<Attachment>) {
        rule.setContent {
            SolventaTheme {
                EvidenciaAvisoScreen(
                    draft = ClaimNoticeDraft(
                        poliza = "POL-1",
                        fechaHecho = "12 mar 2026",
                        descripcion = "Pantalla rota",
                        lugar = "Calle 72",
                        geo = null,
                        locationDenied = false,
                        adjuntos = files,
                    ),
                    onAttach = { _, _ -> },
                    onRemove = {},
                    onCameraDenied = {},
                    onSend = {},
                    onQueue = {},
                )
            }
        }
    }

    private fun jpeg(width: Int = 8, height: Int = 8): ByteArray {
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        bitmap.eraseColor(Color.RED)
        val out = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, out)
        return out.toByteArray()
    }
}
