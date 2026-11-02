package com.grupo8_uniandes.solventa.claim

import androidx.activity.ComponentActivity
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenAssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenProviderCatalog
import com.grupo8_uniandes.solventa.domain.bff.claim.ProviderCatalog
import com.grupo8_uniandes.solventa.ui.shell.AsistenciaSitioScreen
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test

class AsistenciaSitioTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenLocationAllowed_whenAssistanceOpens_thenTheRequestIsVisibleAndCancelReturns() {
        val request = OpenAssistanceRequest()
        val form = request.open(locationAllowed = true)!!
        var onCatalog by mutableStateOf(true)
        rule.setContent {
            SolventaTheme {
                if (onCatalog) {
                    val rows = (OpenProviderCatalog().open(true) as ProviderCatalog.Open).rows
                    MapaPrestadoresScreen(rows = rows, onOpenAssistance = { onCatalog = false })
                } else {
                    AsistenciaSitioScreen(
                        form = form,
                        onContinue = {},
                        onCancel = {
                            request.cancel()
                            onCatalog = true
                        },
                    )
                }
            }
        }

        rule.onNodeWithTag("action_open_provider_0").performClick()
        rule.onNodeWithText("Registramos el pedido con tu ubicación. Operaciones lo ve; no hay despacho real a un taller.")
            .assertIsDisplayed()
        rule.onNodeWithText("POL-88219-CO · Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("12 mar 2026").assertIsDisplayed()
        rule.onNodeWithText("Pantalla rota al caer el teléfono").assertIsDisplayed()
        rule.onNodeWithText("Av. Caracas con Calle 72").assertIsDisplayed()
        rule.onNodeWithText("Pide permiso de ubicacion del dispositivo para geoetiquetar").assertIsDisplayed()
        rule.onNodeWithTag("action_continuar_evidencia").performClick()
        rule.onAllNodesWithTag("screen_evidencia").assertCountEquals(0)
        rule.onNodeWithTag("screen_asistencia_sitio").assertIsDisplayed()
        rule.onNodeWithTag("action_cancelar_asistencia").performClick()
        rule.onNodeWithTag("screen_mapa_prestadores").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_asistencia_sitio").assertCountEquals(0)
    }

    @Test
    fun givenLocationDenied_whenAssistanceIsRequested_thenTheScreenDoesNotOpen() {
        val form = OpenAssistanceRequest().open(locationAllowed = false)
        rule.setContent {
            SolventaTheme {
                if (form != null) {
                    AsistenciaSitioScreen(form = form, onContinue = {}, onCancel = {})
                }
            }
        }

        rule.onAllNodesWithTag("screen_asistencia_sitio").assertCountEquals(0)
    }
}
