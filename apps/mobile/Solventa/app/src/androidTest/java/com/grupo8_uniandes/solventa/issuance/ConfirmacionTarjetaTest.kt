package com.grupo8_uniandes.solventa.issuance

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.compose.material3.Text
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.shell.ConfirmacionTarjetaScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test

class ConfirmacionTarjetaTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenTheReviewOffer_whenShown_thenThePremiumIsReadOnlyAndInicioIsSelected() {
        val viewModel = ConfirmacionTarjetaViewModel(prima = 42_000, moneda = "COP")
        show(viewModel)
        rule.onNodeWithText("Confirma el pago").assertIsDisplayed()
        rule.onNodeWithText("Prima $42.000 COP").assertIsDisplayed()
        rule.onNodeWithText("Solo lectura. La tarjeta no se envía ni se guarda.").assertIsDisplayed()
        rule.onNodeWithText("Se descarta al confirmar").assertIsDisplayed()
        rule.onNodeWithTag("tab_Inicio").assertIsSelected()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)
        rule.onNodeWithTag("field_tarjeta").performTextInput("4242")
        rule.onNodeWithText("Confirmar pago").performClick()
        rule.onNodeWithTag("screen_confirmacion_tarjeta").assertIsDisplayed()
        rule.waitForIdle()
        org.junit.Assert.assertEquals("4242", viewModel.state.value.numero)
    }

    private fun show(viewModel: ConfirmacionTarjetaViewModel) {
        var state by mutableStateOf(viewModel.state.value)
        rule.setContent {
            SolventaTheme {
                Box(Modifier.fillMaxSize()) {
                    Text(stringResource(R.string.card_title))
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
                        onConfirm = { viewModel.confirm() },
                        onBackToOffer = { viewModel.discard() },
                        onLeave = {},
                    )
                    SolventaBottomBar(
                        selected = Destination.Inicio,
                        onSelect = {},
                        modifier = Modifier.align(Alignment.BottomCenter),
                    )
                }
            }
        }
    }
}
