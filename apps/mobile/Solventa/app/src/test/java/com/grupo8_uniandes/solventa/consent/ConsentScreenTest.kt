package com.grupo8_uniandes.solventa.consent

import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertIsOff
import androidx.compose.ui.test.assertIsOn
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.ui.components.SolventaSwitch
import com.grupo8_uniandes.solventa.ui.consent.ConsentBody
import com.grupo8_uniandes.solventa.ui.consent.ConsentScreen
import com.grupo8_uniandes.solventa.ui.consent.ConsentSheet
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class ConsentScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenAlta_whenSwitchTurnsOn_thenConfirmRunsOnce() {
        var confirms = 0
        var backs = 0
        var on by mutableStateOf(false)
        rule.setContent {
            SolventaTheme {
                ConsentScreen(
                    switchOn = on,
                    confirmEnabled = on,
                    onSwitch = { on = it },
                    onConfirm = { confirms += 1 },
                    onBack = { backs += 1 },
                )
            }
        }

        rule.onNodeWithText("Consentimiento").assertIsDisplayed()
        rule.onNodeWithText("Tratamiento de datos").assertIsDisplayed()
        rule.onNodeWithText(
            "Autorizas el tratamiento de tus datos para emitir y administrar tu póliza (habeas data).",
        ).assertIsDisplayed()
        rule.onNodeWithTag("solventa_switch").assertIsOff()
        rule.onNodeWithTag("action_aceptar_continuar").assertIsNotEnabled()
        rule.onNodeWithTag("action_volver").performClick()
        assertEquals(1, backs)
        rule.onNodeWithTag("solventa_switch").performClick()
        rule.waitForIdle()
        rule.onNodeWithTag("solventa_switch").assertIsOn()
        rule.onNodeWithTag("action_aceptar_continuar").performClick()
        assertEquals(1, confirms)
    }

    @Test
    fun givenSheet_whenClose_thenDismissRuns() {
        var closes = 0
        rule.setContent {
            SolventaTheme {
                ConsentSheet(
                    visible = true,
                    switchOn = true,
                    confirmEnabled = false,
                    onSwitch = {},
                    onConfirm = {},
                    onClose = { closes += 1 },
                )
            }
        }

        rule.onNodeWithTag("solventa_bottom_sheet").assertIsDisplayed()
        rule.onNodeWithContentDescription("Cerrar").assertIsDisplayed()
        rule.onNodeWithTag("action_close").performClick()
        assertEquals(1, closes)
    }

    @Test
    fun givenExplicitModifier_whenShown_thenConsentStaysVisible() {
        rule.setContent {
            SolventaTheme {
                Column {
                    ConsentScreen(
                        switchOn = false,
                        confirmEnabled = false,
                        onSwitch = {},
                        onConfirm = {},
                        onBack = {},
                        modifier = Modifier,
                    )
                    ConsentBody(
                        switchOn = true,
                        confirmEnabled = true,
                        onSwitch = {},
                        onConfirm = {},
                        modifier = Modifier,
                    )
                    ConsentSheet(
                        visible = true,
                        switchOn = false,
                        confirmEnabled = false,
                        onSwitch = {},
                        onConfirm = {},
                        onClose = {},
                        modifier = Modifier,
                    )
                }
            }
        }

        rule.onAllNodesWithTag("solventa_switch").assertCountEquals(3)
        rule.onNodeWithTag("solventa_bottom_sheet").assertIsDisplayed()
    }

    @Test
    fun givenLabeledSwitch_whenShown_thenLabelStays() {
        rule.setContent {
            SolventaTheme {
                SolventaSwitch(
                    label = "Tratamiento de datos",
                    checked = false,
                    onCheckedChange = {},
                )
            }
        }

        rule.onNodeWithText("Tratamiento de datos").assertIsDisplayed()
        rule.onNodeWithTag("solventa_switch").assertIsOff()
    }
}
