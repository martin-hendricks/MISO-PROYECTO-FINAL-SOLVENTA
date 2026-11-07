package com.grupo8_uniandes.solventa.claim

import android.Manifest
import android.app.Application
import android.net.Uri
import androidx.activity.compose.LocalActivityResultRegistryOwner
import androidx.activity.result.ActivityResultRegistry
import androidx.activity.result.ActivityResultRegistryOwner
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
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.core.app.ActivityOptionsCompat
import androidx.test.core.app.ApplicationProvider
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
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.shell.AvisoSiniestroScreen
import com.grupo8_uniandes.solventa.ui.shell.ConfirmacionAvisoScreen
import com.grupo8_uniandes.solventa.ui.shell.EvidenciaAvisoScreen
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import kotlinx.coroutines.runBlocking
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import java.io.File

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class AvisoSiniestroScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenACurrentPolicy_whenTheNoticeIsSent_thenSin441ShowsOnce() {
        show(grantCamera = true)
        rule.onNodeWithText("Reportar siniestro · Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("POL-88219-CO · Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("12 mar 2026").assertIsDisplayed()
        rule.onNodeWithText("Pantalla rota al caer el teléfono").assertIsDisplayed()
        rule.onNodeWithText("Av. Caracas con Calle 72").assertIsDisplayed()
        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithTag("tab_Siniestros").assertIsDisplayed()
        rule.onNodeWithTag("claim_send").assertIsNotEnabled()
        rule.onNodeWithTag("claim_take_photo").performClick()
        rule.onNodeWithText("image/jpeg", substring = true).assertIsDisplayed()
        rule.onNodeWithTag("claim_record_video").performClick()
        rule.onNodeWithText("video/mp4", substring = true).assertIsDisplayed()
        rule.onNodeWithText("Foto, video y recibo del daño · evidencia de Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithTag("claim_pick_file").performClick()
        rule.onNodeWithText("dano.jpg").assertIsDisplayed()
        rule.onNodeWithText("Enviar aviso").performClick()
        rule.onNodeWithText("Aviso recibido").assertIsDisplayed()
        rule.onNodeWithText(
            "SIN-441 · Protección de dispositivo · en evaluación. Te avisamos el avance en esta lista.",
        ).assertIsDisplayed()
        rule.onAllNodesWithText("Enviar aviso").assertCountEquals(0)
        rule.onNodeWithText("Ver mis avisos").assertIsDisplayed()
        rule.onNodeWithText("Ir al inicio").assertIsDisplayed()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)
    }

    @Test
    fun givenGeotag_whenLocationIsDeniedThenAllowed_thenTheCoordinateShows() {
        show(permissions = listOf(false, true))
        rule.onNodeWithTag("claim_use_location").assertDoesNotExist()
        rule.onNodeWithTag("claim_geotag").performClick()
        rule.onNodeWithTag("claim_use_location").performClick()
        rule.onNodeWithText("Permiso denegado").assertIsDisplayed()
        rule.onNodeWithText("Puedes enviar el aviso sin geoetiqueta").assertIsDisplayed()
        rule.onNodeWithTag("claim_use_location").performClick()
        rule.onNodeWithText("GPS 4.6533, -74.0836 · ±12 m").assertIsDisplayed()
    }

    @Test
    fun givenTheCameraIsDenied_whenAFileIsPicked_thenTheFlowStaysOpen() {
        show(permissions = listOf(false))
        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithTag("claim_take_photo").performClick()
        rule.onNodeWithText("Cámara denegada").assertIsDisplayed()
        rule.onNodeWithText("Elige una foto de la galería o abre Ajustes").assertIsDisplayed()
        rule.onNodeWithTag("claim_settings").performClick()
        rule.onNodeWithTag("claim_pick_file").performClick()
        rule.onNodeWithText("dano.jpg").assertIsDisplayed()
        rule.onNodeWithTag("claim_remove_dano.jpg").performClick()
        rule.onAllNodesWithText("dano.jpg").assertCountEquals(0)
        rule.onNodeWithTag("claim_pick_file").performClick()
        rule.onNodeWithText("Guardar en cola").performClick()
        rule.onNodeWithTag("claim_queued").assertIsDisplayed()
        rule.onAllNodesWithText("Aviso recibido").assertCountEquals(0)
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()
    }

    @Test
    fun givenPoliciesInForce_whenOneIsChosen_thenThatNumberIsKept() {
        rule.setContent {
            var policy by remember { mutableStateOf("POL-1") }
            SolventaTheme {
                AvisoSiniestroScreen(
                    policies = listOf(
                        WalletEntry("POL-1", "SOAT", "moto", "vigente", "2027-01-01"),
                        WalletEntry("POL-2", "Vida", "amparo", "por_vencer", "2026-12-01"),
                    ),
                    policiesLoaded = true,
                    sentences = listOf(policy, "2026-11-01", "Choque", ""),
                    onRevise = { next, _, _, _ -> policy = next },
                    onContinue = {},
                    onCancel = {},
                )
            }
        }
        rule.onNodeWithTag("claim_policy").performClick()
        rule.onNodeWithTag("claim_policy_option_POL-2").performClick()
        rule.onNodeWithText("POL-2 · Vida").assertIsDisplayed()
    }

    @Test
    fun givenNoPolicies_whenTheFormLoads_thenItSaysSo() {
        rule.setContent {
            SolventaTheme {
                AvisoSiniestroScreen(
                    policiesLoaded = true,
                    onRevise = { _, _, _, _ -> },
                    onContinue = {},
                    onCancel = {},
                )
            }
        }
        rule.onNodeWithTag("claim_no_policy").assertIsDisplayed()
    }

    @Test
    fun givenTheCatalog_whenReportIsChosen_thenTheCallbackRuns() {
        var reported = false
        rule.setContent {
            SolventaTheme {
                MapaPrestadoresScreen(
                    rows = emptyList(),
                    onOpenAssistance = {},
                    onReport = { reported = true },
                )
            }
        }
        rule.onNodeWithText("Reportar siniestro").performClick()
        org.junit.Assert.assertTrue(reported)
    }

    private fun show(permissions: List<Boolean> = listOf(true), grantCamera: Boolean = false) {
        if (grantCamera) {
            shadowOf(ApplicationProvider.getApplicationContext<Application>())
                .grantPermissions(Manifest.permission.CAMERA)
        }
        val registry = CannedEvidenceRegistry(permissions)
        val owner = object : ActivityResultRegistryOwner {
            override val activityResultRegistry = registry
        }
        rule.setContent {
            val notice = remember { OpenClaimNotice(ReadyClaims(), MemoryClaimHold()) { "key-1" } }
            var phase by remember { mutableStateOf(notice.phase) }
            var draft by remember { mutableStateOf(notice.draft) }
            var receipt by remember { mutableStateOf(notice.receipt?.siniestroId) }
            var queued by remember { mutableStateOf(notice.queued) }
            fun refresh() {
                phase = notice.phase
                draft = notice.draft
                receipt = notice.receipt?.siniestroId
                queued = notice.queued
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
                                    runBlocking { notice.send() }
                                    refresh()
                                },
                                onQueue = {
                                    notice.queue()
                                    refresh()
                                },
                                queued = queued,
                                fileRejected = true,
                                rejection = "rechazado",
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

    private class ReadyClaims : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> =
            StandInAnswer.Ready(ClaimReceipt("SIN-441", ClaimStatus.EN_EVALUACION))

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Failed
    }
}

internal class CannedEvidenceRegistry(
    private val permissions: List<Boolean> = listOf(true),
) : ActivityResultRegistry() {
    private var permissionIndex = 0

    override fun <I, O> onLaunch(
        requestCode: Int,
        contract: androidx.activity.result.contract.ActivityResultContract<I, O>,
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
            is ActivityResultContracts.OpenDocument -> sampleFile()
            else -> return
        }
        @Suppress("UNCHECKED_CAST")
        dispatchResult(requestCode, result as O)
    }

    private fun write(uri: Uri) {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val name = uri.lastPathSegment?.substringAfterLast('/').orEmpty()
        if (name.isNotEmpty()) {
            val file = File(context.cacheDir, "claim/$name")
            file.parentFile?.mkdirs()
            file.writeBytes(SAMPLE)
        }
        runCatching { context.contentResolver.openOutputStream(uri)?.use { it.write(SAMPLE) } }
    }

    private fun sampleFile(): Uri {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val file = File(context.cacheDir, "claim/dano.jpg")
        file.parentFile?.mkdirs()
        file.writeBytes(SAMPLE)
        return Uri.fromFile(file)
    }

    private companion object {
        val SAMPLE = byteArrayOf(1, 2, 3, 4)
    }
}
