package com.grupo8_uniandes.solventa.issuance

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performTextInput
import com.grupo8_uniandes.solventa.ui.shell.ConfirmacionTarjetaScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class ConfirmacionTarjetaFormatTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenAFranchisePrefix_whenTheNumberAndMonthAreTyped_thenTheyShowGroupedDigits() {
        val viewModel = ConfirmacionTarjetaViewModel()
        var state by mutableStateOf(viewModel.state.value)
        rule.setContent {
            SolventaTheme {
                ConfirmacionTarjetaScreen(
                    state = state,
                    onTitular = {
                        viewModel.onTitular(it)
                        state = viewModel.state.value
                    },
                    onNumero = {
                        viewModel.onNumero(it)
                        state = viewModel.state.value
                    },
                    onMes = {
                        viewModel.onMes(it)
                        state = viewModel.state.value
                    },
                    onAnio = {
                        viewModel.onAnio(it)
                        state = viewModel.state.value
                    },
                    onCodigo = {
                        viewModel.onCodigo(it)
                        state = viewModel.state.value
                    },
                    onConfirm = {},
                    onBackToOffer = {},
                    onLeave = {},
                )
            }
        }
        rule.onNodeWithText("Camila Restrepo").assertIsDisplayed()
        rule.onNodeWithText("4242 4242 4242 4242").assertIsDisplayed()
        rule.onNodeWithText("08").assertIsDisplayed()
        rule.onNodeWithText("28").assertIsDisplayed()
        rule.onNodeWithText("123").assertIsDisplayed()
        rule.onNodeWithTag("field_tarjeta").performTextInput("378282246310005")
        rule.onAllNodesWithText("4242 4242 4242 4242").assertCountEquals(0)
        rule.onNodeWithText("3782 822463 10005").assertIsDisplayed()
        rule.onNodeWithText("15 dígitos").assertIsDisplayed()
        rule.onNodeWithTag("field_mes").performTextInput("8")
        rule.onNodeWithText("08").assertIsDisplayed()
        rule.onNodeWithText("Mes").assertIsDisplayed()
        rule.onNodeWithText("Año").assertIsDisplayed()
    }
}
