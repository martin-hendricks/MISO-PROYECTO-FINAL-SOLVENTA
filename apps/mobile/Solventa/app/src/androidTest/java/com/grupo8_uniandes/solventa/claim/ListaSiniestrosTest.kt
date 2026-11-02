package com.grupo8_uniandes.solventa.claim

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.shell.SiniestrosScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test

class ListaSiniestrosTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenTheReviewSet_whenTheListOpens_thenEachClaimShowsItsStatusAndNoBell() {
        rule.setContent {
            SolventaTheme {
                Box(Modifier.fillMaxSize()) {
                    SiniestrosScreen(
                        claims = reviewRows(),
                        onOpenClaim = {},
                        onOpenCatalog = {},
                    )
                    SolventaBottomBar(
                        selected = Destination.Siniestros,
                        onSelect = {},
                        modifier = Modifier.align(Alignment.BottomCenter),
                    )
                }
            }
        }

        rule.onNodeWithText("SIN-441").assertIsDisplayed()
        rule.onNodeWithText("Protección de dispositivo · pantalla rota").assertIsDisplayed()
        rule.onAllNodesWithText("En evaluación").assertCountEquals(2)
        rule.onNodeWithText("SIN-220").assertIsDisplayed()
        rule.onAllNodesWithText("Pagado").assertCountEquals(2)
        rule.onNodeWithText("SIN-P01").assertIsDisplayed()
        rule.onNodeWithText("Pago automático · pagado").assertIsDisplayed()
        rule.onNodeWithTag("chip_todos").assertIsSelected()
        rule.onNodeWithText("Inicio").assertIsDisplayed()
        rule.onNodeWithText("Pólizas").assertIsDisplayed()
        rule.onNodeWithText("Siniestros").assertIsDisplayed()
        rule.onNodeWithText("Perfil").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()
        rule.onNodeWithTag("action_open_claim_SIN-441").performClick()
        rule.onAllNodesWithTag("screen_siniestro_detalle").assertCountEquals(0)
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)
        rule.onNodeWithTag("screen_siniestros").assertIsDisplayed()
    }

    private fun reviewRows() = listOf(
        ClaimSummary("SIN-441", "Protección de dispositivo", "pantalla rota", ClaimStatus.EN_EVALUACION),
        ClaimSummary("SIN-220", "Protección de dispositivo", "hurto", ClaimStatus.PAGADO),
        ClaimSummary(
            "SIN-P01",
            "Clima y vuelos",
            "retraso de vuelo",
            ClaimStatus.PAGADO,
            "Pago automático · pagado",
        ),
    )
}
