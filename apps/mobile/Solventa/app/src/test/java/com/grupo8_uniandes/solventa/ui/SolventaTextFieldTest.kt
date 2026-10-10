package com.grupo8_uniandes.solventa.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class SolventaTextFieldTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenOutlinedErrorAndFilledReadOnly_whenEdited_thenOnlyTheOpenFieldChanges() {
        var outlined = ""
        var filled = "fijo"
        rule.setContent {
            SolventaTheme {
                Column {
                    SolventaTextField(
                        value = outlined,
                        onValueChange = { outlined = it },
                        label = "Correo",
                        helper = "El correo no es válido.",
                        modifier = Modifier,
                        style = SolventaFieldStyle.Outlined,
                        state = SolventaFieldState.Error,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                        testTag = "field_correo",
                    )
                    SolventaTextField(
                        value = filled,
                        onValueChange = { filled = it },
                        label = "Contraseña",
                        helper = "",
                        style = SolventaFieldStyle.Filled,
                        state = SolventaFieldState.ReadOnly,
                        visualTransformation = PasswordVisualTransformation(),
                    )
                    SolventaTextField(
                        value = "CC",
                        onValueChange = {},
                        label = "Tipo",
                        helper = "Documento",
                        state = SolventaFieldState.Default,
                        testTag = "field_tipo",
                    )
                }
            }
        }

        rule.onNodeWithText("El correo no es válido.").assertIsDisplayed()
        rule.onNodeWithText("Correo").assertIsDisplayed()
        rule.onNodeWithTag("field_correo").performTextInput("ana")
        rule.onNodeWithTag("solventa_text_field").assertIsDisplayed()
        rule.onNodeWithTag("field_tipo").assertIsDisplayed()
        assertEquals("ana", outlined)
        assertEquals("fijo", filled)
    }
}
