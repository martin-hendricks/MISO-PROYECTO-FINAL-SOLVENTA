package com.grupo8_uniandes.solventa.claim

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertDoesNotExist
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCenter
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderType
import com.grupo8_uniandes.solventa.prestadores.MapaPrestadoresUi
import com.grupo8_uniandes.solventa.prestadores.ProviderMapPhase
import com.grupo8_uniandes.solventa.prestadores.ProviderPlacement
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.shell.SiniestrosScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class MapaPrestadoresTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Before
    fun accessibilityChecks() {
        rule.enableAccessibilityChecks()
    }

    @Test
    fun givenLocationAllowed_whenTheCatalogOpens_thenTheStubRowsAreVisible() {
        rule.setContent {
            SolventaTheme {
                MapaPrestadoresScreen(
                    state = MapaPrestadoresUi(
                        phase = ProviderMapPhase.NearMe,
                        placement = ProviderPlacement.Near,
                        radioKm = 10.0,
                        centro = ProviderCenter(4.65, -74.05, "posicion"),
                        mapsKey = "",
                        providers = listOf(
                            Provider(
                                id = "PRE-1",
                                nombre = "Taller Norte",
                                tipo = ProviderType.TALLER_MOTOS,
                                ramos = listOf("soat-motocicleta"),
                                direccion = "Cra 13",
                                ciudad = "Bogotá",
                                barrio = "Chapinero",
                                lat = 4.65,
                                lng = -74.05,
                                telefono = "601",
                                horario = "Lun",
                                distanciaKm = 1.2,
                            ),
                        ),
                    ),
                    onPermission = {},
                    onSelectCity = {},
                    onSelectRamo = {},
                    onOpenProvider = {},
                )
            }
        }

        rule.onNodeWithText("Taller Norte").assertIsDisplayed()
        rule.onNodeWithText("A 1,2 km").assertIsDisplayed()
        rule.onNodeWithText("Cra 13 · Chapinero · Bogotá").assertIsDisplayed()
        rule.onNodeWithTag("screen_mapa_prestadores").assertIsDisplayed()
    }

    @Test
    fun givenTheClaimsList_whenShown_thenTheCatalogChevronIsAbsent() {
        rule.setContent {
            SolventaTheme {
                SiniestrosScreen(claims = emptyList(), onOpenClaim = {})
            }
        }

        rule.onNodeWithTag("screen_siniestros").assertIsDisplayed()
        rule.onNodeWithTag("action_open_providers").assertIsDisplayed()
        rule.onNodeWithTag("screen_mapa_prestadores").assertDoesNotExist()
    }
}
