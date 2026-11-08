package com.grupo8_uniandes.solventa.accessibility

import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.ui.shell.InicioScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizaDetalleScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizasScreen
import com.grupo8_uniandes.solventa.ui.shell.SiniestroDetalleScreen
import com.grupo8_uniandes.solventa.ui.shell.SiniestrosScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import com.grupo8_uniandes.solventa.policy.PolicyDetailUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class DestinationSemanticsTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenPolizas_whenShown_thenHeading() {
        rule.setContent {
            SolventaTheme {
                PolizasScreen(policies = emptyList(), onOpenPolicy = {}, onNewQuote = {})
            }
        }
        rule.onNode(isHeading() and hasText("Polizas")).assertExists()
    }

    @Test
    fun givenPolizaDetalle_whenShown_thenHeading() {
        rule.setContent {
            SolventaTheme {
                PolizaDetalleScreen(state = PolicyDetailUiState(numero = "POL-1"))
            }
        }
        rule.onNode(isHeading()).assertExists()
    }

    @Test
    fun givenSiniestros_whenAClaimIsShown_thenTheCardIsOneNamedButton() {
        rule.setContent {
            SolventaTheme {
                SiniestrosScreen(
                    claims = listOf(
                        ClaimSummary(
                            siniestroId = "SIN-1",
                            ramo = "SOAT",
                            resumen = "Choque",
                            estado = ClaimStatus.PAGADO,
                            estadoTexto = "Pagado",
                        ),
                    ),
                    onOpenClaim = {},
                    onOpenCatalog = {},
                )
            }
        }
        val card = rule.onNodeWithTag("action_open_claim_SIN-1").fetchSemanticsNode()
        assertEquals(Role.Button, card.config[SemanticsProperties.Role])
        val spoken = card.config[SemanticsProperties.Text].joinToString(" ") { it.text }
        assertTrue(spoken.contains("Pagado"))
    }

    @Test
    fun givenSiniestroDetalle_whenShown_thenHeading() {
        rule.setContent {
            SolventaTheme {
                SiniestroDetalleScreen(claimId = "SIN-1", onBack = {})
            }
        }
        rule.onNode(isHeading() and hasText("Siniestros")).assertExists()
    }

    @Test
    fun givenInicioFailed_whenShown_thenFailureIsALiveRegion() {
        rule.setContent {
            SolventaTheme {
                InicioScreen(state = HomeUiState(failed = true), onNewQuote = {})
            }
        }
        val node = rule.onNodeWithText("No se pudo cargar la información.").fetchSemanticsNode()
        assertEquals(
            androidx.compose.ui.semantics.LiveRegionMode.Polite,
            node.config[SemanticsProperties.LiveRegion],
        )
    }
}
