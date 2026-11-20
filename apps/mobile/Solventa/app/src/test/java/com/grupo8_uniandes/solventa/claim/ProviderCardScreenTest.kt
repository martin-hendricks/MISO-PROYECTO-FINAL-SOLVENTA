package com.grupo8_uniandes.solventa.claim

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCenter
import com.grupo8_uniandes.solventa.prestadores.CameraTarget
import com.grupo8_uniandes.solventa.prestadores.MapaPrestadoresUi
import com.grupo8_uniandes.solventa.prestadores.ProviderMapPhase
import com.grupo8_uniandes.solventa.prestadores.ProviderPlacement
import com.grupo8_uniandes.solventa.prestadores.sample
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class ProviderCardScreenTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenATappedMarker_whenTheCardOpens_thenItReplacesTheSheetAndBackClosesIt() {
        var opened: String? = null
        var directions: String? = null
        var called: String? = null
        var requested: String? = null
        var state by mutableStateOf(mapState(ProviderMapPhase.NearMe))
        show(
            state = { state },
            onOpenProvider = { opened = it },
            onCloseCard = { state = state.copy(selectedIds = emptyList()) },
            onDirections = { directions = it },
            onCall = { called = it },
            onRequestAssistance = { requested = it },
        )

        rule.onNodeWithTag("providers_sheet").assertIsDisplayed()
        state = state.copy(selectedIds = listOf("PRE-BOG-06"))

        rule.onNodeWithTag("provider_card").assertIsDisplayed()
        rule.onNodeWithTag("providers_sheet").assertDoesNotExist()
        rule.onNodeWithTag("providers_distance_label").assertTextEquals("A 0,9 km")
        rule.onNodeWithText("Cómo llegar").performScrollTo().performClick()
        rule.onNodeWithText("Llamar").performScrollTo().performClick()
        rule.onNodeWithText("Pedir asistencia").performScrollTo().performClick()
        rule.onNodeWithTag("provider_card_name_0").performScrollTo().performClick()
        assertEquals("PRE-BOG-06", directions)
        assertEquals("601 555 0112", called)
        assertEquals("PRE-BOG-06", requested)
        assertEquals("PRE-BOG-06", opened)

        rule.activityRule.scenario.onActivity { it.onBackPressedDispatcher.onBackPressed() }
        rule.onNodeWithTag("provider_card").assertDoesNotExist()
        rule.onNodeWithTag("providers_sheet").assertIsDisplayed()
    }

    @Test
    fun givenAClaimCard_whenShowingDistance_thenItIsMeasuredFromTheEvent() {
        val state = mapState(ProviderMapPhase.ClaimMode).copy(
            placement = ProviderPlacement.Claim,
            centro = ProviderCenter(4.626, -74.15, "siniestro"),
            selectedIds = listOf("PRE-BOG-06"),
        )
        show(state = { state })

        rule.onNodeWithTag("providers_distance_label").performScrollTo().assertTextEquals("A 0,9 km del evento")
    }

    @Test
    fun givenDeniedLocation_whenACityShows_thenTheSheetNamesItAndOffersLocation() {
        val state = mapState(ProviderMapPhase.ChooseCity).copy(
            placement = ProviderPlacement.City,
            centro = null,
            ciudad = "Bogotá",
        )
        show(state = { state })

        rule.onNodeWithText("Prestadores en Bogotá").assertIsDisplayed()
        rule.onNodeWithTag("providers_enable_location").assertIsDisplayed()
        rule.onNodeWithTag("providers_distance_label").assertDoesNotExist()
    }

    @Test
    fun givenAPartialArea_whenTheMapShows_thenTheTruncationNoticeIsVisible() {
        val state = mapState(ProviderMapPhase.NearMe).copy(truncado = true)
        show(state = { state })

        rule.onNodeWithText("Acerca el mapa para ver todos los prestadores.").assertIsDisplayed()
    }

    private fun show(
        state: () -> MapaPrestadoresUi,
        onOpenProvider: (String) -> Unit = {},
        onCloseCard: () -> Unit = {},
        onDirections: (String) -> Unit = {},
        onCall: (String) -> Unit = {},
        onRequestAssistance: (String) -> Unit = {},
    ) {
        rule.setContent {
            SolventaTheme {
                MapaPrestadoresScreen(
                    state = state(),
                    onPermission = {},
                    onSelectCity = {},
                    onSelectRamo = {},
                    onOpenProvider = onOpenProvider,
                    onCloseCard = onCloseCard,
                    onDirections = { onDirections(it.id) },
                    onCall = onCall,
                    onRequestAssistance = onRequestAssistance,
                    mapSlot = { modifier, onLoaded ->
                        LaunchedEffect(Unit) { onLoaded() }
                        Box(modifier.testTag("providers_map_slot"))
                    },
                )
            }
        }
    }
}

private fun mapState(phase: ProviderMapPhase) = MapaPrestadoresUi(
    phase = phase,
    placement = ProviderPlacement.Near,
    centro = ProviderCenter(4.6432, -74.0631, "posicion"),
    mapsKey = "test",
    markedCity = "Bogotá",
    cameraTarget = CameraTarget(4.6432, -74.0631, 14f),
    providers = listOf(sample("PRE-BOG-06", 0.9)),
)
