package com.grupo8_uniandes.solventa.registration

import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assert
import androidx.compose.ui.test.assertHeightIsAtLeast
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.ui.registration.LivenessCameraContent
import com.grupo8_uniandes.solventa.ui.registration.LivenessPhase
import com.grupo8_uniandes.solventa.ui.registration.LivenessScreen
import com.grupo8_uniandes.solventa.ui.registration.LivenessUiState
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class LivenessScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenSavedFields_whenContinuar_thenCopyMatchesAndTheStepAdvances() {
        var continued = 0
        rule.setContent {
            SolventaTheme {
                LivenessScreen(
                    state = LivenessUiState(
                        givenName = "Camila",
                        surnames = "Restrepo",
                        email = "camila@correo.com",
                        documentType = "CC",
                        documentTypeOptions = listOf("CC", "CE", "PA"),
                        documentNumber = "1023456789",
                        password = "secret",
                    ),
                    onGivenName = {},
                    onSurnames = {},
                    onEmail = {},
                    onDocumentType = {},
                    onDocumentNumber = {},
                    onPassword = {},
                    onContinue = { continued += 1 },
                    onExistingAccount = {},
                )
            }
        }

        rule.onNodeWithTag("screen_prueba_de_vida").assertIsDisplayed()
        rule.onNodeWithText("Paso 4 de 4 · Prueba de vida").assertIsDisplayed()
        rule.onNodeWithText("Prueba de vida").assertIsDisplayed()
        rule.onNodeWithText(
            "Una selfie confirma que eres tú. Si la verificación simulada no pasa, sigues con tu documento.",
        ).assertIsDisplayed()
        rule.onNodeWithText("Camila").assertIsDisplayed()
        rule.onNodeWithTag("action_liveness_continuar").performScrollTo().performClick()
        assertEquals(1, continued)
    }

    @Test
    fun givenCamera_whenShown_thenTheShutterIsNamedAndAtLeast48dp() {
        show(LivenessPhase.Camera)
        rule.onNodeWithTag("liveness_camera_title").assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.Heading))
        rule.onNodeWithContentDescription("Cara dentro de la elipse").assertIsDisplayed()
        rule.onNodeWithTag("action_liveness_shutter").assertHeightIsAtLeast(48.dp)
        rule.onNodeWithContentDescription("Tomar foto").assertExists()
    }

    @Test
    fun givenSending_whenShown_thenTheStatusIsLiveAndTheShutterIsDisabled() {
        show(LivenessPhase.Sending, photo = byteArrayOf(1))
        rule.onNodeWithTag("liveness_status").assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.LiveRegion))
        rule.onNodeWithText("Verificando la foto").assertIsDisplayed()
        rule.onNodeWithTag("action_liveness_shutter").assertIsNotEnabled()
    }

    @Test
    fun givenPassed_whenShown_thenContinuarIsAtLeast48dp() {
        show(LivenessPhase.Passed, photo = TINY_JPEG)
        rule.onNodeWithContentDescription("Foto tomada", useUnmergedTree = true).assertExists()
        rule.onNodeWithTag("action_liveness_continuar_camara").performScrollTo().assertHeightIsAtLeast(48.dp)
    }

    @Test
    fun givenFailed_whenShown_thenRepeatAndDocumentAreOffered() {
        show(LivenessPhase.Failed)
        rule.onNodeWithText("La verificación simulada no pasó.").assertIsDisplayed()
        rule.onNodeWithTag("liveness_status").assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.LiveRegion))
        rule.onNodeWithTag("action_liveness_repetir").performScrollTo().assertHeightIsAtLeast(48.dp)
        rule.onNodeWithTag("action_liveness_documento").performScrollTo().assertHeightIsAtLeast(48.dp)
    }

    @Test
    fun givenDenied_whenShown_thenThereIsNoPreview() {
        show(LivenessPhase.Denied)
        rule.onNodeWithText("Sin permiso de cámara. Puedes seguir con el documento que ya cargaste.").assertIsDisplayed()
        rule.onNodeWithTag("liveness_camera_preview").assertDoesNotExist()
        rule.onNodeWithTag("action_liveness_repetir").performScrollTo().assertHeightIsAtLeast(48.dp)
    }

    @Test
    fun givenUnavailable_whenShown_thenRetryIsOffered() {
        show(LivenessPhase.Unavailable, photo = byteArrayOf(1))
        rule.onNodeWithText("No pudimos verificar la foto. Reintenta.").assertIsDisplayed()
        rule.onNodeWithTag("action_liveness_reintentar").performScrollTo().assertHeightIsAtLeast(48.dp)
        rule.onNodeWithTag("action_liveness_ya_tengo_cuenta").performScrollTo().assertHeightIsAtLeast(48.dp)
    }

    private fun show(phase: LivenessPhase, photo: ByteArray? = null) {
        rule.setContent {
            SolventaTheme {
                LivenessCameraContent(
                    state = LivenessUiState(phase = phase, photo = photo),
                    onShutter = {},
                    onRepeat = {},
                    onRetry = {},
                    onContinue = {},
                    onContinueWithDocument = {},
                    onExistingAccount = {},
                    preview = {},
                )
            }
        }
    }

    private companion object {
        val TINY_JPEG: ByteArray = android.util.Base64.decode(
            "/9j/4AAQSkZJRgABAQAASABIAAD/4QBMRXhpZgAATU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAAaADAAQAAAABAAAAAQAAAAD/7QA4UGhvdG9zaG9wIDMuMAA4QklNBAQAAAAAAAA4QklNBCUAAAAAABDUHYzZjwCyBOmACZjs+EJ+/8AAEQgAAQABAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+v/EAB8BAAMBAQEBAQEBAQEAAAAAAAABAgMEBQYHCAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMRBAUhMQYSQVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz9PX29/j5+v/bAEMAAgICAgICAwICAwUDAwMFBgUFBQUGCAYGBgYGCAoICAgICAgKCgoKCgoKCgwMDAwMDA4ODg4ODw8PDw8PDw8PD//bAEMBAgICBAQEBwQEBxALCQsQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEP/dAAQAAf/aAAwDAQACEQMRAD8A+L6KKK/lM/38P//Z",
            android.util.Base64.DEFAULT,
        )
    }
}
