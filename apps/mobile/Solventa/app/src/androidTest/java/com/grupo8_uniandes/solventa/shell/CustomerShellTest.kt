package com.grupo8_uniandes.solventa.shell

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsNotSelected
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.grupo8_uniandes.solventa.MainActivity
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class CustomerShellTest {
    @get:Rule
    val rule = createAndroidComposeRule<MainActivity>()

    @Test
    fun givenSignedIn_whenShellOpens_thenExactlyFourDestinations() {
        listOf("Inicio", "Pólizas", "Siniestros", "Perfil").forEach { label ->
            assertTrue(rule.onAllNodesWithText(label).fetchSemanticsNodes().isNotEmpty())
        }
        listOf("Inicio", "Polizas", "Siniestros", "Perfil").forEach { name ->
            rule.onNodeWithTag("tab_$name").assertIsDisplayed()
        }
        val inicio = rule.onNodeWithTag("tab_Inicio").fetchSemanticsNode().boundsInRoot.left
        val polizas = rule.onNodeWithTag("tab_Polizas").fetchSemanticsNode().boundsInRoot.left
        val siniestros = rule.onNodeWithTag("tab_Siniestros").fetchSemanticsNode().boundsInRoot.left
        val perfil = rule.onNodeWithTag("tab_Perfil").fetchSemanticsNode().boundsInRoot.left
        assertTrue(inicio < polizas && polizas < siniestros && siniestros < perfil)
        rule.onAllNodesWithText("Favoritos").assertCountEquals(0)
        rule.onAllNodesWithText("Open Finance").assertCountEquals(0)
        rule.onAllNodesWithText("Notificaciones").assertCountEquals(0)
        rule.onNodeWithTag("tab_Inicio").assertIsSelected()
        rule.onNodeWithTag("tab_Siniestros").assertIsNotSelected()
        listOf("Inicio", "Polizas", "Siniestros", "Perfil").forEach { name ->
            assertTrue(
                rule.onAllNodesWithTag("icon_$name", useUnmergedTree = true)
                    .fetchSemanticsNodes()
                    .isNotEmpty(),
            )
        }
    }

    @Test
    fun givenInicio_whenPolizasTapped_thenPolizasIsSelected() {
        rule.onNodeWithText("Pólizas").performClick()
        rule.onNodeWithTag("screen_polizas").assertIsDisplayed()
        rule.onNodeWithTag("tab_Polizas").assertIsSelected()
    }

    @Test
    fun givenPolicyDetail_whenVolver_thenReturnsToPolizasNotInicio() {
        rule.onNodeWithText("Pólizas").performClick()
        rule.onNodeWithTag("action_open_policy").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithTag("tab_Polizas").assertIsSelected()
        rule.onNodeWithTag("action_volver").performClick()
        rule.onNodeWithTag("screen_polizas").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
    }

    @Test
    fun givenSelectedDestination_whenTappedAgain_thenStaysOnRoot() {
        rule.onNodeWithText("Pólizas").performClick()
        rule.onNodeWithTag("action_open_policy").performClick()
        rule.onNodeWithText("Pólizas").performClick()
        rule.onNodeWithTag("screen_polizas").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_poliza_detalle").assertCountEquals(0)
    }

    @Test
    fun givenRoot_whenSystemBack_thenDestinationDoesNotChange() {
        rule.onNodeWithText("Pólizas").performClick()
        rule.runOnIdle {
            rule.activity.onBackPressedDispatcher.onBackPressed()
        }
        rule.onNodeWithTag("tab_Polizas").assertIsSelected()
        rule.onNodeWithTag("screen_polizas").assertIsDisplayed()
    }

    @Test
    fun givenInicio_whenNuevaCotizacion_thenInicioStaysSelected() {
        rule.onNodeWithText("Nueva cotización").performClick()
        rule.onNodeWithTag("screen_cotizacion").assertIsDisplayed()
        rule.onNodeWithTag("tab_Inicio").assertIsSelected()
        rule.onAllNodesWithText("Favoritos").assertCountEquals(0)
    }

    @Test
    fun givenOfferAccepted_whenIssuingAndIssued_thenBarIsHiddenUntilLeaving() {
        rule.onNodeWithText("Nueva cotización").performClick()
        rule.onNodeWithText("Aceptar oferta").performClick()
        rule.onNodeWithTag("screen_emision").assertIsDisplayed()
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onNodeWithTag("action_finish_issuing").performClick()
        rule.onNodeWithTag("screen_issued").assertIsDisplayed()
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onNodeWithTag("action_issued_home").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
        rule.onNodeWithTag("tab_Inicio").assertIsSelected()
    }

    @Test
    fun givenIssuedPolicy_whenContinueToDetail_thenPolizasIsSelected() {
        rule.onNodeWithText("Nueva cotización").performClick()
        rule.onNodeWithText("Aceptar oferta").performClick()
        rule.onNodeWithTag("action_finish_issuing").performClick()
        rule.onNodeWithTag("action_issued_policy").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithTag("tab_Polizas").assertIsSelected()
    }

    @Test
    fun givenPerfil_whenOpened_thenOnlyIdiomaYRegion() {
        rule.onNodeWithText("Perfil").performClick()
        rule.onNodeWithText("Idioma y región").assertIsDisplayed()
        rule.onAllNodesWithTag("profile_entry").assertCountEquals(1)
    }

    @Test
    fun givenQuoteAndDetail_whenShown_thenTheyShareControls() {
        rule.onNodeWithText("Nueva cotización").performClick()
        rule.onNodeWithTag("solventa_button_filled").assertIsDisplayed()
        rule.onNodeWithTag("solventa_button_outlined").assertIsDisplayed()
        rule.onNodeWithTag("solventa_text_field").assertIsDisplayed()
        rule.onNodeWithTag("solventa_card").assertIsDisplayed()
        rule.onNodeWithTag("bottom_bar").assertIsDisplayed()
        rule.onNodeWithText("Cancelar").performClick()
        rule.onNodeWithText("Pólizas").performClick()
        rule.onNodeWithTag("action_open_policy").performClick()
        rule.onNodeWithTag("solventa_button_filled").assertIsDisplayed()
        rule.onNodeWithTag("solventa_button_outlined").assertIsDisplayed()
        rule.onNodeWithTag("solventa_text_field").assertIsDisplayed()
        rule.onNodeWithTag("solventa_card").assertIsDisplayed()
        rule.onNodeWithTag("bottom_bar").assertIsDisplayed()
    }
}
