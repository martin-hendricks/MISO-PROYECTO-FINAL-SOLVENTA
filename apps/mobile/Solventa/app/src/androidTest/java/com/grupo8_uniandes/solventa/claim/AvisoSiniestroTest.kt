package com.grupo8_uniandes.solventa.claim

import android.net.Uri
import androidx.activity.ComponentActivity
import androidx.activity.compose.LocalActivityResultRegistryOwner
import androidx.activity.result.ActivityResultRegistry
import androidx.activity.result.ActivityResultRegistryOwner
import androidx.activity.result.contract.ActivityResultContract
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.core.app.ActivityOptionsCompat
import androidx.test.platform.app.InstrumentationRegistry
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.domain.bff.claim.MemoryClaimHold
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.shell.AvisoSiniestroScreen
import com.grupo8_uniandes.solventa.ui.shell.ConfirmacionAvisoScreen
import com.grupo8_uniandes.solventa.ui.shell.EvidenciaAvisoScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import java.io.File

class AvisoSiniestroTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Before
    fun accessibilityChecks() {
        rule.enableAccessibilityChecks()
    }

    @Test
    fun givenACurrentPolicy_whenTheNoticeIsSent_thenSin441ShowsOnceAndSiniestrosStaysSelected() {
        show()
        rule.onNodeWithText("Reportar siniestro").assertIsDisplayed()
        rule.onNodeWithText("Elige una póliza").assertIsDisplayed()
        rule.onNodeWithText("Selecciona la fecha").assertIsDisplayed()
        rule.onNodeWithText("Cuenta qué pasó").assertIsDisplayed()
        rule.onNodeWithText("Escribe el lugar").assertIsDisplayed()
        rule.onNodeWithText("Continuar a evidencia").assertIsDisplayed()
        rule.onNodeWithText("Cancelar").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)

        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithText("Foto, video y recibo del daño · evidencia de Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("Tomar foto").assertIsDisplayed()
        rule.onNodeWithText("Grabar video").assertIsDisplayed()
        rule.onNodeWithText("Adjuntar archivo").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()
        rule.onNodeWithTag("claim_pick_file").performClick()
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
        rule.onNodeWithTag("claim_pick_file").performClick()
        rule.onNodeWithText("Guardar en cola").performClick()
        rule.onAllNodesWithText("Aviso recibido").assertCountEquals(0)
        rule.onNodeWithTag("screen_evidencia_aviso").assertIsDisplayed()
    }

    @Test
    fun givenLocationAndCamera_whenTheyAreDenied_thenTheNoticeStaysOpen() {
        show(permissions = listOf(false, true, false))
        rule.onNodeWithTag("claim_geotag").performScrollTo().performClick()
        rule.onNodeWithText("Permiso denegado").performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("Puedes enviar el aviso sin geoetiqueta").performScrollTo().assertIsDisplayed()
        rule.onNodeWithTag("claim_geotag").performClick()
        rule.onNodeWithTag("claim_geotag").performClick()
        rule.onNodeWithText("GPS 4.6533, -74.0836 · ±12 m").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()

        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithTag("claim_record_video").performClick()
        rule.onNodeWithText("Cámara denegada").assertIsDisplayed()
        rule.onNodeWithTag("claim_settings").assertIsDisplayed()
        rule.onNodeWithTag("screen_evidencia_aviso").assertIsDisplayed()
    }

    private fun show(permissions: List<Boolean> = listOf(true)) {
        val owner = object : ActivityResultRegistryOwner {
            override val activityResultRegistry = DeviceEvidenceRegistry(permissions)
        }
        rule.setContent {
            val notice = remember {
                OpenClaimNotice(ReadyClaims(), MemoryClaimHold()) { "key-1" }.also { opened ->
                    val sample = com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNoticeDraft.Review
                    opened.revise(sample.poliza, sample.fechaHecho, sample.descripcion, sample.lugar)
                }
            }
            var phase by remember { mutableStateOf(notice.phase) }
            var draft by remember { mutableStateOf(notice.draft) }
            var receipt by remember { mutableStateOf(notice.receipt?.siniestroId) }
            fun refresh() {
                phase = notice.phase
                draft = notice.draft
                receipt = notice.receipt?.siniestroId
            }
            CompositionLocalProvider(LocalActivityResultRegistryOwner provides owner) {
                SolventaTheme {
                    Box(Modifier.fillMaxSize()) {
                        when (phase) {
                            NoticePhase.Form -> Column {
                                Text(stringResource(R.string.claim_notice_title))
                                AvisoSiniestroScreen(
                                    geotag = draft.geotag,
                                    geo = draft.geo,
                                    locationDenied = draft.locationDenied,
                                    onToggleGeotag = {
                                        notice.setGeotag(it)
                                        refresh()
                                    },
                                    onUseLocation = {
                                        notice.placeAt(GeoPoint(4.6533, -74.0836, 12))
                                        refresh()
                                    },
                                    onLocationDenied = {
                                        notice.placeAt(null)
                                        refresh()
                                    },
                                    onContinue = {
                                        notice.continueToEvidence()
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
                                draft = draft,
                                onAttach = { attachment, bytes ->
                                    notice.attachFile(attachment, bytes)
                                    refresh()
                                },
                                onRemove = {
                                    notice.remove(it)
                                    refresh()
                                },
                                onCameraDenied = {
                                    notice.markCameraDenied()
                                    refresh()
                                },
                                onSend = {
                                    notice.sendBlocking()
                                    refresh()
                                },
                                onQueue = {
                                    notice.queue()
                                    refresh()
                                },
                            )
                        }
                        if (phase != NoticePhase.Closed) {
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

private class DeviceEvidenceRegistry(
    private val permissions: List<Boolean>,
) : ActivityResultRegistry() {
    private var permissionIndex = 0

    override fun <I, O> onLaunch(
        requestCode: Int,
        contract: ActivityResultContract<I, O>,
        input: I,
        options: ActivityOptionsCompat?,
    ) {
        val result: Any? = when (contract) {
            is ActivityResultContracts.RequestPermission -> {
                val granted = permissions.getOrElse(permissionIndex) { permissions.last() }
                permissionIndex += 1
                granted
            }
            is ActivityResultContracts.TakePicture,
            is ActivityResultContracts.CaptureVideo,
            -> {
                write(input as Uri)
                true
            }
            is ActivityResultContracts.PickVisualMedia -> sampleFile("foto.jpg")
            is ActivityResultContracts.OpenDocument -> sampleFile("dano.jpg")
            else -> return
        }
        @Suppress("UNCHECKED_CAST")
        dispatchResult(requestCode, result as O)
    }

    private fun write(uri: Uri) {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val name = uri.lastPathSegment?.substringAfterLast('/').orEmpty()
        if (name.isNotEmpty()) {
            val file = File(context.cacheDir, "claim/$name")
            file.parentFile?.mkdirs()
            file.writeBytes(SAMPLE)
        }
        runCatching { context.contentResolver.openOutputStream(uri)?.use { it.write(SAMPLE) } }
    }

    private fun sampleFile(name: String): Uri {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val file = File(context.cacheDir, "claim/$name")
        file.parentFile?.mkdirs()
        file.writeBytes(SAMPLE)
        return Uri.fromFile(file)
    }

    private companion object {
        val SAMPLE = byteArrayOf(1, 2, 3, 4)
    }
}
