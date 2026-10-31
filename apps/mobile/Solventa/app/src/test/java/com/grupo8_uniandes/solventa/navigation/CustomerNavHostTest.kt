package com.grupo8_uniandes.solventa.navigation

import android.Manifest
import android.app.Application
import androidx.compose.foundation.layout.PaddingValues
import androidx.test.core.app.ApplicationProvider
import org.robolectric.Shadows.shadowOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
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
            panel = HomePanel(offerId = "SOAT", policyId = "POL-9"),
        ))

        val nav = holder[0]!!
        rule.onNodeWithText("SOAT").assertIsDisplayed()
        rule.onNodeWithText("POL-9").assertIsDisplayed()
        rule.onNodeWithText("Nueva cotización").performClick()
        nav.openDestination(Destination.Inicio)
        rule.waitForIdle()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
        rule.onNodeWithTag("action_accept_offer").performClick()
        rule.onNodeWithTag("screen_issued").assertIsDisplayed()
        rule.onNodeWithTag("action_issued_home").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()

        rule.onNodeWithText("Nueva cotización").performClick()
        rule.onNodeWithTag("action_cancel_quote").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()

        rule.onNodeWithTag("action_accept_offer").performClick()
        rule.onNodeWithTag("action_issued_policy").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        nav.popBackStack()
        rule.waitForIdle()
        rule.onNodeWithTag("screen_polizas").assertIsDisplayed()
        rule.onNodeWithTag("action_open_policy_POL-88219-CO").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithTag("policy_numero").assertTextEquals("POL-88219-CO")

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

    @Test
    fun givenLocationAllowed_whenTheCatalogOpens_thenAssistanceReturnsToTheCatalog() {
        shadowOf(ApplicationProvider.getApplicationContext<Application>())
            .grantPermissions(Manifest.permission.ACCESS_FINE_LOCATION)
        val holder = arrayOfNulls<NavHostController>(1)
        show(holder, start = SiniestrosRoute)

        rule.onNodeWithTag("action_open_catalog").performClick()
        rule.onNodeWithTag("screen_mapa_prestadores").assertIsDisplayed()
        rule.onNodeWithText("Taller Norte").assertIsDisplayed()
        assertEquals(MapaPrestadoresRoute, holder[0]!!.currentBackStackEntry!!.toSolventaRoute())

        rule.onNodeWithTag("action_open_provider_0").performClick()
        rule.onNodeWithTag("screen_asistencia_sitio").assertIsDisplayed()
        rule.onNodeWithText("Av. Caracas con Calle 72").assertIsDisplayed()
        rule.onNodeWithTag("action_continuar_evidencia").performClick()
        rule.onNodeWithTag("screen_asistencia_sitio").assertIsDisplayed()
        assertEquals(AsistenciaSitioRoute, holder[0]!!.currentBackStackEntry!!.toSolventaRoute())

        rule.onNodeWithTag("action_cancelar_asistencia").performClick()
        rule.onNodeWithTag("screen_mapa_prestadores").assertIsDisplayed()
        assertEquals(MapaPrestadoresRoute, holder[0]!!.currentBackStackEntry!!.toSolventaRoute())
    }

    @Test
    fun givenSiniestros_whenANoticeIsSent_thenTheConfirmationShowsSin441() {
        val holder = arrayOfNulls<NavHostController>(1)
        show(holder, start = InicioRoute)
        holder[0]!!.navigate(SiniestrosRoute)
        rule.waitForIdle()
        rule.onNodeWithText("Reportar siniestro").performClick()
        rule.onNodeWithTag("screen_aviso_siniestro").assertIsDisplayed()
        assertEquals(AvisoSiniestroRoute, holder[0]!!.currentBackStackEntry!!.toSolventaRoute())
        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithTag("screen_evidencia_aviso").assertIsDisplayed()
        assertEquals(EvidenciaAvisoRoute, holder[0]!!.currentBackStackEntry!!.toSolventaRoute())
        rule.onNodeWithText("Mientras usas la app").performClick()
        rule.onNodeWithText("Enviar aviso").performClick()
        rule.waitForIdle()
        rule.onNodeWithTag("screen_confirmacion_aviso").assertIsDisplayed()
        rule.onNodeWithText(
            "SIN-441 · Protección de dispositivo · en evaluación. Te avisamos el avance en esta lista.",
        ).assertIsDisplayed()
        val sent = holder[0]!!.currentBackStackEntry!!.toSolventaRoute()
        assertEquals(ConfirmacionAvisoRoute("SIN-441"), sent)
        rule.onNodeWithText("Ver mis avisos").performClick()
        rule.waitForIdle()
        rule.onNodeWithTag("screen_siniestros").assertIsDisplayed()
        rule.onNodeWithText("Reportar siniestro").performClick()
        rule.onNodeWithText("Continuar a evidencia").performClick()
        rule.onNodeWithText("Mientras usas la app").performClick()
        rule.onNodeWithText("Enviar aviso").performClick()
        rule.waitForIdle()
        rule.onNodeWithText("Ir al inicio").performClick()
        rule.waitForIdle()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
        holder[0]!!.navigate(SiniestrosRoute)
        rule.waitForIdle()
        rule.onNodeWithText("Reportar siniestro").performClick()
        rule.onNodeWithText("Cancelar").performClick()
        rule.waitForIdle()
        rule.onNodeWithTag("screen_siniestros").assertIsDisplayed()
    }

    @Test
    fun givenRejection_whenHome_thenInicioOpens() {
        show(start = SuscripcionRechazadaRoute)
        rule.onNodeWithTag("screen_rejection").assertIsDisplayed()
        rule.onNodeWithText("No pudimos emitir Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithTag("action_rejection_home").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
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
