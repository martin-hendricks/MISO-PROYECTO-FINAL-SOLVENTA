package com.grupo8_uniandes.solventa.claim

import androidx.activity.ComponentActivity
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderType
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenAssistanceRequest
import com.grupo8_uniandes.solventa.prestadores.MapaPrestadoresUi
import com.grupo8_uniandes.solventa.prestadores.ProviderMapPhase
import com.grupo8_uniandes.solventa.prestadores.ProviderPlacement
import com.grupo8_uniandes.solventa.ui.shell.AsistenciaSitioScreen
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class AsistenciaSitioTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Before
    fun accessibilityChecks() {
        rule.enableAccessibilityChecks()
    }

    @Test
    fun givenLocationAllowed_whenAssistanceOpens_thenTheRequestIsVisibleAndCancelReturns() {
        val request = OpenAssistanceRequest()
        val form = request.open(locationAllowed = true)!!
        var onCatalog by mutableStateOf(true)
        rule.setContent {
            SolventaTheme {
                if (onCatalog) {
                    MapaPrestadoresScreen(
                        state = MapaPrestadoresUi(
                            phase = ProviderMapPhase.NearMe,
                            placement = ProviderPlacement.Near,
                            mapsKey = "",
                            providers = listOf(
                                Provider(
                                    id = "PRE-BOG-06",
                                    nombre = "Taller Moto Chapinero",
                                    tipo = ProviderType.TALLER_MOTOS,
                                    ramos = listOf("soat-motocicleta"),
                                    direccion = "Cra 13 #45-18",
                                    ciudad = "Bogotá",
                                    barrio = "Chapinero",
                                    lat = 4.6355,
                                    lng = -74.0655,
                                    telefono = "601 555 0112",
                                    horario = "Lun–Sáb 7:00–19:00",
                                    distanciaKm = 0.9,
                                ),
                            ),
                        ),
                        onPermission = {},
                        onSelectCity = {},
                        onSelectTipo = {},
                        onOpenProvider = { onCatalog = false },
                    )
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
