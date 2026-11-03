package com.grupo8_uniandes.solventa.claim

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.material3.Text
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.MemoryClaimHold
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.shell.AvisoSiniestroScreen
import com.grupo8_uniandes.solventa.ui.shell.ConfirmacionAvisoScreen
import com.grupo8_uniandes.solventa.ui.shell.EvidenciaAvisoScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test

class AvisoSiniestroTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenACurrentPolicy_whenTheNoticeIsSent_thenSin441ShowsOnceAndSiniestrosStaysSelected() {
        show()
        rule.onNodeWithText("Reportar siniestro · Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("POL-88219-CO · Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("12 mar 2026").assertIsDisplayed()
        rule.onNodeWithText("Pantalla rota al caer el teléfono").assertIsDisplayed()
        rule.onNodeWithText("Av. Caracas con Calle 72").assertIsDisplayed()
        rule.onNodeWithText("Continuar a evidencia").assertIsDisplayed()
        rule.onNodeWithText("Cancelar").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)

        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithText("No graba video", substring = true).assertIsDisplayed()
        rule.onAllNodesWithTag("tab_Siniestros").assertCountEquals(0)
        rule.onNodeWithText("Mientras usas la app").performClick()
        rule.onNodeWithText("Foto, video y recibo del daño · evidencia de Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("Enviar aviso").assertIsDisplayed()
        rule.onNodeWithText("Guardar en cola").assertIsDisplayed()
        rule.onNodeWithText("Encuadra el soporte. El recorte se adjunta al aviso.").assertIsDisplayed()
        rule.onNodeWithText("Adjuntar al trámite").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()

        rule.onNodeWithText("Enviar aviso").performClick()
        rule.onNodeWithText("Aviso recibido").assertIsDisplayed()
        rule.onNodeWithText(
            "SIN-441 · Protección de dispositivo · en evaluación. Te avisamos el avance en esta lista.",
        ).assertIsDisplayed()
        rule.onAllNodesWithText("Enviar aviso").assertCountEquals(0)
        rule.onNodeWithTag("screen_confirmacion_aviso").assertIsDisplayed()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)
    }

    @Test
    fun givenTheQueue_whenItIsSaved_thenTheReceiptIsNotShown() {
        show()
        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithText("Mientras usas la app").performClick()
        rule.onNodeWithText("Guardar en cola").performClick()
        rule.onAllNodesWithText("Aviso recibido").assertCountEquals(0)
        rule.onNodeWithTag("screen_evidencia_aviso").assertIsDisplayed()
    }

    @Test
    fun givenLocationAndCamera_whenTheyAreDenied_thenTheNoticeStaysOpen() {
        show()
        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithText("Mientras usas la app").performClick()
        rule.onNodeWithTag("claim_location_row").performClick()
        rule.onNodeWithText("Dónde ocurrió el siniestro").assertIsDisplayed()
        rule.onAllNodesWithTag("tab_Siniestros").assertCountEquals(0)
        rule.onNodeWithTag("claim_permission_deny").performClick()
        rule.onNodeWithText("Permiso denegado").assertIsDisplayed()
        rule.onNodeWithText("Puedes enviar el aviso sin geoetiqueta").assertIsDisplayed()
        rule.onNodeWithText("Enviar aviso").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()

        rule.onNodeWithTag("claim_location_row").performClick()
        rule.onNodeWithText("Mientras usas la app").performClick()
        rule.onNodeWithText("GPS 4.6533, -74.0836 · ±12 m · Bogotá").assertIsDisplayed()
    }

    @Test
    fun givenTheCameraIsDenied_whenPhotosAreOffered_thenTheFlowStaysOnSiniestros() {
        show()
        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithTag("claim_permission_deny").performClick()
        rule.onNodeWithText("Cámara denegada").assertIsDisplayed()
        rule.onNodeWithText("Elegir de fotos").assertIsDisplayed()
        rule.onNodeWithText("Abrir ajustes del dispositivo").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()
        rule.onNodeWithText("Elegir de fotos").performClick()
        rule.onNodeWithText("Permitir todas").assertIsDisplayed()
        rule.onAllNodesWithTag("tab_Siniestros").assertCountEquals(0)
        rule.onNodeWithTag("claim_permission_deny").performClick()
        rule.onNodeWithTag("screen_evidencia_aviso").assertIsDisplayed()
    }

    private fun show() {
        rule.setContent {
            val notice = remember { OpenClaimNotice(ReadyClaims(), MemoryClaimHold()) { "key-1" } }
            var phase by remember { mutableStateOf(notice.phase) }
            var draft by remember { mutableStateOf(notice.draft) }
            var receipt by remember { mutableStateOf(notice.receipt?.siniestroId) }
            fun refresh() {
                phase = notice.phase
                draft = notice.draft
                receipt = notice.receipt?.siniestroId
            }
            SolventaTheme {
                Box(Modifier.fillMaxSize()) {
                    when (phase) {
                        NoticePhase.Form -> Column {
                            Text(stringResource(R.string.claim_notice_title))
                            AvisoSiniestroScreen(
                            onContinue = {
                                notice.continueToCamera()
                                refresh()
                            },
                            onCancel = {
                                notice.cancel()
                                refresh()
                            },
                        )
                        }
                        NoticePhase.Confirmation -> ConfirmacionAvisoScreen(
                            siniestroId = receipt.orEmpty(),
                            onMyClaims = {},
                            onHome = {},
                        )
                        else -> EvidenciaAvisoScreen(
                            phase = phase,
                            draft = draft,
                            onAllowCamera = { notice.allowCamera(); refresh() },
                            onDenyCamera = { notice.denyCamera(); refresh() },
                            onDismissCamera = { notice.dismissCamera(); refresh() },
                            onAllowPhotos = { notice.allowPhotos(); refresh() },
                            onDenyPhotos = { notice.denyPhotos(); refresh() },
                            onAllowLocation = { notice.allowLocation(); refresh() },
                            onDenyLocation = { notice.denyLocation(); refresh() },
                            onDismissLocation = { notice.dismissLocation(); refresh() },
                            onOpenLocation = { notice.openLocation(); refresh() },
                            onChoosePhotos = { notice.choosePhotos(); refresh() },
                            onSend = {
                                notice.sendBlocking()
                                refresh()
                            },
                            onQueue = {
                                notice.queue()
                                refresh()
                            },
                            onAttach = {
                                notice.attachSupport()
                                refresh()
                            },
                        )
                    }
                    val tabsHidden = phase == NoticePhase.Camera ||
                        phase == NoticePhase.Photos ||
                        phase == NoticePhase.Location
                    if (!tabsHidden && phase != NoticePhase.Closed) {
                        SolventaBottomBar(
                            selected = Destination.Siniestros,
                            onSelect = {},
                            modifier = Modifier.align(Alignment.BottomCenter),
                        )
                    }
                }
            }
        }
    }

    private fun OpenClaimNotice.sendBlocking() {
        kotlinx.coroutines.runBlocking { send() }
    }

    private class ReadyClaims : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> =
            StandInAnswer.Ready(ClaimReceipt("SIN-441", ClaimStatus.EN_EVALUACION))

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Failed
    }
}
