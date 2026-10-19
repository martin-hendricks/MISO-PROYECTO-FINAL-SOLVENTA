package com.grupo8_uniandes.solventa.navigation

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import com.grupo8_uniandes.solventa.home.HomeSummary
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.home.OfferSummary
import com.grupo8_uniandes.solventa.home.PolicySummary
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class CustomerNavHostTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenDefaultStart_whenShown_thenInicio() {
        rule.setContent {
            SolventaTheme {
                CustomerNavHost(
                    navController = rememberNavController(),
                    homeState = HomeUiState(),
                    contentPadding = PaddingValues(0.dp),
                )
            }
        }

        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
    }

    @Test
    fun givenProfileStart_whenShown_thenPerfil() {
        rule.setContent {
            SolventaTheme {
                CustomerNavHost(
                    navController = rememberNavController(),
                    homeState = HomeUiState(),
                    contentPadding = PaddingValues(8.dp),
                    modifier = Modifier,
                    startDestination = PerfilRoute,
                )
            }
        }

        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
    }

    @Test
    fun givenAQuote_whenIssued_thenHomeAndThePolicyStayReachable() {
        val holder = arrayOfNulls<NavHostController>(1)
        show(holder, HomeUiState(
            summary = HomeSummary(
                offer = OfferSummary("SOAT"),
                policy = PolicySummary("POL-9"),
            ),
        ))

        val nav = holder[0]!!
        rule.onNodeWithText("SOAT").assertIsDisplayed()
        rule.onNodeWithText("POL-9").assertIsDisplayed()
        rule.onNodeWithText("Nueva cotización").performClick()
        nav.openDestination(Destination.Inicio)
        rule.waitForIdle()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
        rule.onNodeWithText("Nueva cotización").performClick()
        rule.onNodeWithTag("solventa_text_field").performTextInput("ABC12")
        rule.onNodeWithText("Aceptar oferta").performClick()
        rule.onNodeWithTag("action_finish_issuing").performClick()
        rule.onNodeWithTag("action_issued_home").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()

        rule.onNodeWithText("Nueva cotización").performClick()
        rule.onNodeWithText("Cancelar").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()

        rule.onNodeWithText("Nueva cotización").performClick()
        rule.onNodeWithText("Aceptar oferta").performClick()
        rule.onNodeWithTag("action_finish_issuing").performClick()
        rule.onNodeWithTag("action_issued_policy").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithTag("solventa_text_field").performTextInput("nota")
        rule.onNodeWithText("Cancelar").performClick()
        rule.onNodeWithTag("screen_polizas").assertIsDisplayed()
        rule.onNodeWithTag("action_open_policy").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()

        nav.openDestination(Destination.Polizas)
        rule.waitForIdle()
        nav.openDestination(Destination.Siniestros)
        rule.waitForIdle()
        rule.onNodeWithTag("screen_siniestros").assertIsDisplayed()
        nav.openDestination(Destination.Siniestros)
        nav.openDestination(Destination.Perfil)
        rule.waitForIdle()
        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
    }

    private fun show(
        holder: Array<NavHostController?> = arrayOfNulls(1),
        homeState: HomeUiState = HomeUiState(),
        start: Any = InicioRoute,
    ) {
        rule.setContent {
            SolventaTheme {
                val controller = rememberNavController()
                holder[0] = controller
                CustomerNavHost(
                    navController = controller,
                    homeState = homeState,
                    contentPadding = PaddingValues(0.dp),
                    startDestination = start,
                )
            }
        }
    }
}
