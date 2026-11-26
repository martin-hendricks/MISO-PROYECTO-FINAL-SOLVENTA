package com.grupo8_uniandes.solventa.prestadores

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderType
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class MapaPrestadoresScreenTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenTwoTypesWithoutAMap_whenAChipIsChosen_thenTheListKeepsThatType() {
        val taller = sample("PRE-BOG-06", 0.9)
        val grua = taller.copy(id = "PRE-GRUA", tipo = ProviderType.GRUA, nombre = "Grúa Laureles")
        var state by mutableStateOf(loaded(mapsKey = "", providers = listOf(taller, grua)))
        show(state = { state }, onSelectTipo = { state = state.copy(tipo = it) })

        rule.onNodeWithText("Taller Moto Chapinero").assertIsDisplayed()
        rule.onNodeWithTag("tipo_grua").performScrollTo().performClick()
        rule.onNodeWithText("Grúa Laureles").assertIsDisplayed()
        rule.onAllNodesWithText("Taller Moto Chapinero").assertCountEquals(0)
        rule.onNodeWithTag("tipo_todos").performScrollTo().performClick()
        rule.onNodeWithText("Taller Moto Chapinero").assertIsDisplayed()
    }

    @Test
    fun givenNoMatchWithoutAMap_whenTheTypeIsChosen_thenTheEmptyNoticeShows() {
        val taller = sample("PRE-BOG-06", 0.9)
        show(
            state = {
                loaded(mapsKey = "", providers = listOf(taller)).copy(tipo = ProviderType.GRUA)
            },
        )

        rule.onNodeWithTag("providers_type_empty").assertIsDisplayed()
        rule.onAllNodesWithText("Taller Moto Chapinero").assertCountEquals(0)
    }

    @Test
    fun givenNoMatchOnTheMap_whenTheTypeIsChosen_thenTheNoticeReplacesTheSheet() {
        val taller = sample("PRE-BOG-06", 0.9)
        show(
            state = {
                loaded(mapsKey = "test", providers = listOf(taller)).copy(tipo = ProviderType.GRUA)
            },
            map = true,
        )

        rule.onNodeWithTag("providers_type_empty").assertIsDisplayed()
        rule.onAllNodesWithTag("providers_sheet").assertCountEquals(0)
    }

    @Test
    fun givenAMatchingTypeOnTheMap_whenTheSheetOpens_thenItListsOnlyThatType() {
        val taller = sample("PRE-BOG-06", 0.9)
        val grua = taller.copy(id = "PRE-GRUA", tipo = ProviderType.GRUA, nombre = "Grúa Laureles")
        show(
            state = {
                loaded(mapsKey = "test", providers = listOf(taller, grua)).copy(tipo = ProviderType.GRUA)
            },
            map = true,
        )

        rule.onNodeWithTag("providers_sheet").assertIsDisplayed()
        rule.onNodeWithTag("action_open_provider_0").performScrollTo().assertIsDisplayed()
        rule.onAllNodesWithTag("action_open_provider_1").assertCountEquals(0)
        rule.onAllNodesWithText("Taller Moto Chapinero").assertCountEquals(0)
    }

    private fun show(
        state: () -> MapaPrestadoresUi,
        onSelectTipo: (ProviderType?) -> Unit = {},
        map: Boolean = false,
    ) {
        rule.setContent {
            SolventaTheme {
                MapaPrestadoresScreen(
                    state = state(),
                    onPermission = {},
                    onSelectCity = {},
                    onSelectTipo = onSelectTipo,
                    onOpenProvider = {},
                    mapSlot = if (!map) {
                        null
                    } else {
                        { modifier, onLoaded ->
                            LaunchedEffect(Unit) { onLoaded() }
                            Box(modifier.testTag("providers_map_slot"))
                        }
                    },
                )
            }
        }
    }

    private fun loaded(mapsKey: String, providers: List<Provider>) = MapaPrestadoresUi(
        phase = ProviderMapPhase.NearMe,
        placement = ProviderPlacement.Near,
        mapsKey = mapsKey,
        providers = providers,
    )
}
