package com.grupo8_uniandes.solventa.accessibility

import androidx.compose.foundation.layout.Column
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertIsOff
import androidx.compose.ui.test.assertIsOn
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.sp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaChip
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaFloatingAction
import com.grupo8_uniandes.solventa.ui.components.SolventaIconButton
import com.grupo8_uniandes.solventa.ui.components.SolventaListRow
import com.grupo8_uniandes.solventa.ui.components.SolventaSkeleton
import com.grupo8_uniandes.solventa.ui.components.SolventaStatus
import com.grupo8_uniandes.solventa.ui.components.SolventaStatusIcon
import com.grupo8_uniandes.solventa.ui.components.SolventaSwitch
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.components.SolventaTopBar
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class SharedControlSemanticsTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenTopBar_whenShown_thenTitleIsHeadingAndBackIsNamed() {
        rule.setContent {
            SolventaTheme {
                SolventaTopBar(title = "Solventa", showBack = true, onBack = {})
            }
        }
        rule.onNode(hasText("Solventa") and isHeading()).assertExists()
        rule.onNode(hasContentDescription("Volver")).assertExists()
        rule.onNode(hasRole(Role.Button) and hasContentDescription("Volver")).assertExists()
    }

    @Test
    fun givenButtons_whenShown_thenRoleAndDisabledState() {
        rule.setContent {
            SolventaTheme {
                Column {
                    SolventaButton("Lleno", SolventaButtonStyle.Filled, {})
                    SolventaButton("Contorno", SolventaButtonStyle.Outlined, {}, enabled = false)
                    SolventaIconButton(
                        icon = painterResource(R.drawable.back),
                        contentDescription = "Cerrar",
                        onClick = {},
                    )
                }
            }
        }
        rule.onNode(hasRole(Role.Button) and hasText("Lleno")).assertExists()
        rule.onNodeWithText("Contorno").assertIsNotEnabled()
        rule.onNodeWithContentDescription("Cerrar").assertExists()
        rule.assertTouchAtLeast(hasContentDescription("Cerrar"))
    }

    @Test
    fun givenRowAndCard_whenClickable_thenOneButtonStop() {
        rule.setContent {
            SolventaTheme {
                Column {
                    SolventaListRow(label = "Póliza", value = "Vigente", onClick = {})
                    SolventaCard(onClick = {}) {
                        androidx.compose.material3.Text("Tarjeta vigente")
                    }
                }
            }
        }
        val row = rule.onNodeWithText("Póliza").fetchSemanticsNode()
        val texts = row.config[SemanticsProperties.Text].map { it.text }
        assertTrue(texts.contains("Póliza"))
        assertTrue(texts.contains("Vigente"))
        assertEquals(Role.Button, row.config[SemanticsProperties.Role])
        rule.onNode(hasRole(Role.Button) and hasText("Tarjeta vigente")).assertExists()
    }

    @Test
    fun givenSwitchAndSkeletonAndAction_whenShown_thenNamedOnce() {
        rule.setContent {
            SolventaTheme {
                Column {
                    SolventaSwitch(label = "Avisos", checked = true, onCheckedChange = {})
                    SolventaSkeleton()
                    SolventaFloatingAction(
                        label = "Avisar",
                        icon = painterResource(R.drawable.add),
                        onClick = {},
                    )
                }
            }
        }
        rule.onNode(hasRole(Role.Switch) and hasText("Avisos")).assertIsOn()
        rule.onNodeWithContentDescription("Cargando").assertExists()
        rule.onNodeWithText("Avisar").assertExists()
    }

    @Test
    fun givenSwitchOff_whenShown_thenOff() {
        rule.setContent {
            SolventaTheme {
                SolventaSwitch(label = "Avisos", checked = false, onCheckedChange = {})
            }
        }
        rule.onNode(hasRole(Role.Switch) and hasText("Avisos")).assertIsOff()
    }

    @Test
    fun givenBottomBarAndChip_whenSelected_thenTabAndCheckbox() {
        rule.setContent {
            SolventaTheme {
                Column {
                    SolventaBottomBar(selected = Destination.Inicio, onSelect = {})
                    SolventaChip(label = "Activo", selected = true, onClick = {})
                }
            }
        }
        rule.onNodeWithTag("tab_Inicio").assertIsSelected()
        rule.onNode(hasRole(Role.Tab) and hasText("Inicio")).assertExists()
        rule.onNode(hasRole(Role.Checkbox) and hasText("Activo")).assertIsSelected()
        rule.assertTouchAtLeast(hasRole(Role.Checkbox) and hasText("Activo"))
        rule.assertTouchAtLeast(hasTestTag("tab_Inicio"))
        assertEquals(12.sp, SolventaTypography.material.labelMedium.fontSize)
    }

    @Test
    fun givenStatus_whenShown_thenWordOnceAndNoImageName() {
        rule.setContent {
            SolventaTheme {
                SolventaStatusIcon(
                    status = SolventaStatus.Success,
                    word = "Pagado",
                    icon = painterResource(R.drawable.check),
                )
            }
        }
        rule.onNodeWithText("Pagado").assertExists()
        rule.onAllNodes(hasContentDescription("Pagado")).fetchSemanticsNodes()
            .let { assertEquals(0, it.size) }
    }

    @Test
    fun givenFieldInErrorAndPassword_whenShown_thenErrorAndPassword() {
        rule.setContent {
            SolventaTheme {
                Column {
                    SolventaTextField(
                        value = "",
                        onValueChange = {},
                        label = "Correo",
                        helper = "El correo no es válido.",
                        state = SolventaFieldState.Error,
                    )
                    SolventaTextField(
                        value = "secreto",
                        onValueChange = {},
                        label = "Contraseña",
                        helper = "",
                        visualTransformation = PasswordVisualTransformation(),
                        externalLabel = true,
                    )
                }
            }
        }
        rule.onNode(hasError("El correo no es válido.")).assertExists()
        rule.onNode(isPassword()).assertExists()
    }
}
