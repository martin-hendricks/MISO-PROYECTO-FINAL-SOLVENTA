package com.grupo8_uniandes.solventa.home

import android.content.res.Configuration
import androidx.activity.ComponentActivity
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.ui.shell.SignedInShell
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import java.util.Locale

class InicioTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenPolicyShortcut_whenOpened_thenDetailKeepsPolizasAndVolverReturnsToTheList() {
        show(HomeUiState(panel = HomePanel(policyId = "POL-9")))
        rule.onNodeWithTag("home_policy").performScrollTo().performClick()
        rule.waitForTag("screen_poliza_detalle")
        rule.onNodeWithText("POL-9").assertIsDisplayed()
        rule.onNodeWithTag("tab_Polizas").assertIsSelected()
        rule.onNodeWithTag("action_volver").performClick()
        rule.waitForTag("screen_polizas")
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
        rule.onNodeWithTag("tab_Polizas").assertIsSelected()
    }

    @Test
    fun givenClaimShortcut_whenOpened_thenDetailKeepsSiniestrosAndVolverReturnsToTheList() {
        show(HomeUiState(panel = HomePanel(claimId = "CLM-9")))
        rule.onNodeWithTag("home_claim").performScrollTo().performClick()
        rule.waitForTag("screen_siniestro_detalle")
        rule.onNodeWithText("CLM-9").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()
        rule.onNodeWithTag("action_volver").performClick()
        rule.waitForTag("screen_siniestros")
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()
    }

    @Test
    fun givenOffer_whenAccepted_thenIssuanceShowsThatIdAndHidesTheBar() {
        show(HomeUiState(panel = HomePanel(offerId = "Q-42")))
        rule.onNodeWithTag("action_accept_offer").performScrollTo().performClick()
        rule.waitForTag("screen_emision")
        rule.onNodeWithTag("emision_body").assertIsDisplayed()
        rule.onAllNodesWithText("Q-42").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_cotizacion").assertCountEquals(0)
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
    }

    @Test
    fun givenInicio_whenNuevaCotizacion_thenQuoteOpensAndInicioStaysSelected() {
        show(HomeUiState(panel = HomePanel(offerId = "Q-42")))
        rule.onNodeWithTag("action_new_quote").performScrollTo().performClick()
        rule.waitForTag("screen_cotizacion")
        rule.onAllNodesWithTag("screen_emision").assertCountEquals(0)
        rule.onNodeWithTag("tab_Inicio").assertIsSelected()
        rule.onNodeWithTag("bottom_bar").assertIsDisplayed()
    }

    @Test
    fun givenOrigination_whenVidaTapped_thenInicioStaysAndPerfilOmitsIt() {
        show(HomeUiState(panel = HomePanel(vidaCrediticia = true)))
        rule.onNodeWithText("Vida Crediticia").assertIsDisplayed()
        rule.onNodeWithTag("home_vida_crediticia").performScrollTo().performClick()
        rule.waitForTag("screen_inicio")
        rule.onAllNodesWithTag("screen_cotizacion").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_emision").assertCountEquals(0)
        rule.onNodeWithTag("tab_Perfil").performClick()
        rule.waitForTag("screen_perfil")
        rule.onAllNodesWithText("Vida Crediticia").assertCountEquals(0)
        rule.onAllNodesWithTag("home_vida_crediticia").assertCountEquals(0)
    }

    @Test
    fun givenNoOrigination_whenInicioShows_thenVidaIsAbsent() {
        show(HomeUiState())
        rule.waitForTag("screen_inicio")
        rule.onAllNodesWithText("Vida Crediticia").assertCountEquals(0)
        rule.onAllNodesWithTag("home_vida_crediticia").assertCountEquals(0)
    }

    @Test
    fun givenEachLocale_whenInicioShows_thenSpanishCopy() {
        val panel = HomeUiState(
            panel = HomePanel(
                offerId = "Q-1",
                policyId = "POL-1",
                claimId = "CLM-1",
                vidaCrediticia = true,
            ),
        )
        val localeTag = mutableStateOf("es-CO")
        rule.setContent {
            val locale = Locale.forLanguageTag(localeTag.value)
            Locale.setDefault(locale)
            val base = LocalContext.current
            val config = Configuration(base.resources.configuration)
            config.setLocale(locale)
            val localized = base.createConfigurationContext(config)
            CompositionLocalProvider(
                LocalContext provides localized,
                LocalConfiguration provides config,
            ) {
                SolventaTheme {
                    SignedInShell(homeState = panel)
                }
            }
        }
        listOf("es-CO", "es-MX", "es-CL", "es-PE").forEach { tag ->
            rule.runOnIdle { localeTag.value = tag }
            rule.waitForTag("screen_inicio")
            rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
            check(rule.onAllNodesWithText("Inicio").fetchSemanticsNodes().isNotEmpty())
            rule.onNodeWithText("Aceptar oferta").assertIsDisplayed()
            rule.onNodeWithText("Nueva cotización").assertIsDisplayed()
            rule.onNodeWithText("Detalle de póliza").performScrollTo().assertIsDisplayed()
            rule.onNodeWithText("Vida Crediticia").performScrollTo().assertIsDisplayed()
        }
    }

    private fun show(state: HomeUiState) {
        rule.setContent {
            SolventaTheme {
                SignedInShell(homeState = state)
            }
        }
    }
}

private fun ComposeTestRule.waitForTag(tag: String) {
    waitUntil(timeoutMillis = 30_000) {
        onAllNodesWithTag(tag).fetchSemanticsNodes().isNotEmpty()
    }
}
