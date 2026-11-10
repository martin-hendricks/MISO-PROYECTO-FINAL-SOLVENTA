package com.grupo8_uniandes.solventa.navigation

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import androidx.navigation.compose.rememberNavController
import com.grupo8_uniandes.solventa.domain.push.PushTarget
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.ui.shell.CustomerShell
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class PushNavigationTest {
    @get:Rule
    val rule = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    @Test
    fun givenASignedInShell_whenTheTargetIsAPolicy_thenThatDetailOpens() {
        val holder = arrayOfNulls<NavHostController>(1)
        show(holder, PushTarget.PolizaDetalle("POL-2026-00000002"))
        rule.waitForIdle()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        assertEquals(
            PolizaDetalleRoute("POL-2026-00000002"),
            holder[0]!!.currentBackStackEntry!!.toSolventaRoute(),
        )
    }

    @Test
    fun givenASignedInShell_whenTheTargetIsInicio_thenHomeOpens() {
        val holder = arrayOfNulls<NavHostController>(1)
        show(holder, PushTarget.Inicio, start = PerfilRoute)
        rule.waitForIdle()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
        assertEquals(InicioRoute, holder[0]!!.currentBackStackEntry!!.toSolventaRoute())
    }

    @Test
    fun givenATargetWhileSignedOut_whenSignInSucceeds_thenThePolicyOpens() {
        var signedIn by mutableStateOf(false)
        rule.setContent {
            SolventaTheme {
                CustomerShell(
                    signedOut = !signedIn,
                    enterSignedInShell = signedIn,
                    pushTarget = PushTarget.PolizaDetalle("POL-2026-00000002"),
                )
            }
        }
        rule.onNodeWithTag("screen_login").assertIsDisplayed()
        signedIn = true
        rule.waitForIdle()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithText("POL-2026-00000002").assertIsDisplayed()
    }

    private fun show(
        holder: Array<NavHostController?>,
        target: PushTarget,
        start: Any = InicioRoute,
    ) {
        rule.setContent {
            SolventaTheme {
                val controller = rememberNavController()
                holder[0] = controller
                CustomerNavHost(
                    navController = controller,
                    homeState = HomeUiState(),
                    contentPadding = PaddingValues(0.dp),
                    startDestination = start,
                    pushTarget = target,
                )
            }
        }
    }
}
