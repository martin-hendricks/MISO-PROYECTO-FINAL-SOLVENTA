package com.grupo8_uniandes.solventa.claim

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimDetail
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimEvidence
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimHistory
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimPayment
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.ui.shell.SiniestroDetalleScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class SiniestroDetalleScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenARejectedClaim_whenShown_thenTheTimelineEvidenceAndPolicyAreVisible() {
        var openedPolicy = ""
        var openedUrl = ""
        rule.setContent {
            SolventaTheme {
                SiniestroDetalleScreen(
                    claimId = "interno",
                    claim = ClaimDetail(
                        summary = ClaimSummary(
                            siniestroId = "SIN-9",
                            ramo = "SOAT motocicleta",
                            resumen = "Choque",
                            estado = ClaimStatus.DECIDIDO,
                            resultado = "rechazado",
                            fecha = "2026-03-12",
                            reserva = 350000.0,
                            moneda = "COP",
                        ),
                        poliza = "POL-1",
                        descripcion = "Choque",
                        lugar = "Calle 72",
                        geo = GeoPoint(4.65, -74.08, 12),
                        motivo = "Póliza no vigente",
                        evidencia = listOf(
                            ClaimEvidence("dano.png", "foto", "image/png", "https://example.test/dano.png"),
                            ClaimEvidence("acta.pdf", "soporte", "application/pdf", "https://example.test/acta.pdf"),
                        ),
                        historial = listOf(ClaimHistory("decidido", "2026-03-13", "Decidido")),
                        pago = ClaimPayment("CMP-1", 350000.0, "COP", "2026-03-13"),
                        umbral = null,
                    ),
                    onOpenPolicy = { openedPolicy = it },
                    onOpenEvidence = { openedUrl = it },
                )
            }
        }
        rule.onNodeWithText("Rechazado").assertIsDisplayed()
        rule.onNodeWithTag("claim_reject_reason").assertIsDisplayed()
        rule.onNodeWithTag("claim_lugar").assertIsDisplayed()
        rule.onNodeWithTag("claim_pago").assertIsDisplayed()
        rule.onNodeWithTag("claim_history_decidido").assertIsDisplayed()
        rule.onNodeWithTag("claim_evidence_dano.png").performClick()
        rule.onNodeWithTag("claim_policy").performClick()
        assertEquals("https://example.test/dano.png", openedUrl)
        assertEquals("POL-1", openedPolicy)
    }

    @Test
    fun givenAMissingClaim_whenShown_thenTheNotFoundCopyStays() {
        rule.setContent {
            SolventaTheme {
                SiniestroDetalleScreen(claimId = "no", missing = true)
            }
        }
        rule.onNodeWithTag("claim_not_found").assertIsDisplayed()
    }
}
