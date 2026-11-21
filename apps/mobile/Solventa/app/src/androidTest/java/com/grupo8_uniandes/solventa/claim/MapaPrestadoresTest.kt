package com.grupo8_uniandes.solventa.claim

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCenter
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderType
import com.grupo8_uniandes.solventa.prestadores.CameraTarget
import com.grupo8_uniandes.solventa.prestadores.MapaPrestadoresUi
import com.grupo8_uniandes.solventa.prestadores.ProviderMapPhase
import com.grupo8_uniandes.solventa.prestadores.ProviderPlacement
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.shell.SiniestrosScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
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
    fun givenATappedMarker_whenTheCardOpens_thenItReplacesTheSheetAndBackClosesIt() {
        var opened: String? = null
        var directions: String? = null
        var called: String? = null
        var requested: String? = null
        var state by mutableStateOf(
            MapaPrestadoresUi(
                phase = ProviderMapPhase.NearMe,
                placement = ProviderPlacement.Near,
                centro = ProviderCenter(4.65, -74.05, "posicion"),
                mapsKey = "test",
                cameraTarget = CameraTarget(4.65, -74.05, 14f),
                providers = listOf(NORTE),
            ),
        )
        rule.setContent {
            SolventaTheme {
                MapaPrestadoresScreen(
                    state = state,
                    onPermission = {},
                    onSelectCity = {},
                    onSelectRamo = {},
                    onOpenProvider = { opened = it },
                    onCloseCard = { state = state.copy(selectedIds = emptyList()) },
                    onDirections = { directions = it.id },
                    onCall = { called = it },
                    onRequestAssistance = { requested = it },
                    mapSlot = { modifier, onLoaded ->
                        LaunchedEffect(Unit) { onLoaded() }
                        Box(modifier.testTag("providers_map_slot"))
                    },
                )
            }
        }

        rule.onNodeWithTag("providers_sheet").assertIsDisplayed()
        state = state.copy(selectedIds = listOf("PRE-1"))

        rule.onNodeWithTag("provider_card").assertIsDisplayed()
        rule.onNodeWithTag("providers_sheet").assertDoesNotExist()
        rule.onNodeWithText("Cómo llegar").performScrollTo().performClick()
        rule.onNodeWithText("Llamar").performScrollTo().performClick()
        rule.onNodeWithText("Pedir asistencia").performScrollTo().performClick()
        rule.onNodeWithTag("provider_card_name_0").performScrollTo().performClick()
        assertEquals("PRE-1", directions)
        assertEquals("601", called)
        assertEquals("PRE-1", requested)
        assertEquals("PRE-1", opened)

        rule.activityRule.scenario.onActivity { it.onBackPressedDispatcher.onBackPressed() }
        rule.onNodeWithTag("provider_card").assertDoesNotExist()
        rule.onNodeWithTag("providers_sheet").assertIsDisplayed()
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

private val NORTE = Provider(
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
)
