package com.grupo8_uniandes.solventa.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.test.assertHasNoClickAction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.text.input.PasswordVisualTransformation
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBanner
import com.grupo8_uniandes.solventa.ui.components.SolventaBannerStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomSheet
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaChip
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFloatingAction
import com.grupo8_uniandes.solventa.ui.components.SolventaIconButton
import com.grupo8_uniandes.solventa.ui.components.SolventaIconButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaSelect
import com.grupo8_uniandes.solventa.ui.components.SolventaSkeleton
import com.grupo8_uniandes.solventa.ui.components.SolventaStatus
import com.grupo8_uniandes.solventa.ui.components.SolventaStatusIcon
import com.grupo8_uniandes.solventa.ui.components.SolventaSwitch
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.components.SolventaTopBar
import com.grupo8_uniandes.solventa.ui.registration.OnboardingPhotoInjector
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h4000dp")
class ShellComponentTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenEachVariant_whenShown_thenTheControlAnswers() {
        val selected = mutableStateOf(Destination.Inicio)
        val expanded = mutableStateOf(false)
        val choice = mutableStateOf("CC")
        var clicks = 0
        val chip = mutableStateOf(false)
        val checked = mutableStateOf(false)
        val sheet = mutableStateOf(true)
        val field = mutableStateOf("")
        rule.setContent {
            SolventaTheme(darkTheme = true) {
                Column {
                    SolventaTheme(darkTheme = false) {
                        Text("claro")
                    }
                    SolventaBottomBar(selected = selected.value, onSelect = { selected.value = it })
                    SolventaButton("Lleno", SolventaButtonStyle.Filled, { clicks += 1 })
                    SolventaButton("Tonal", SolventaButtonStyle.Tonal, { clicks += 1 })
                    SolventaButton("Contorno", SolventaButtonStyle.Outlined, { clicks += 1 }, enabled = false)
                    SolventaButton("Texto", SolventaButtonStyle.Text, { clicks += 1 })
                    SolventaChip("Filtro", selected = chip.value, onClick = { chip.value = !chip.value })
                    SolventaChip("Activo", selected = true, onClick = {})
                    SolventaStatus.entries.forEach { status ->
                        SolventaStatusIcon(
                            status = status,
                            word = status.name,
                            icon = painterResource(R.drawable.info),
                        )
                    }
                    SolventaBanner("Info", SolventaBannerStyle.Info)
                    SolventaBanner("Error", SolventaBannerStyle.Error)
                    SolventaCard { Text("Tarjeta") }
                    SolventaSkeleton()
                    SolventaFloatingAction("Flotante", painterResource(R.drawable.add), { clicks += 1 })
                    SolventaIconButton(
                        icon = painterResource(R.drawable.back),
                        contentDescription = "volver",
                        onClick = { clicks += 1 },
                        style = SolventaIconButtonStyle.Default,
                    )
                    SolventaIconButton(
                        icon = painterResource(R.drawable.back),
                        contentDescription = "superficie",
                        onClick = { clicks += 1 },
                        style = SolventaIconButtonStyle.OnSurface,
                        testTag = "icon_on_surface",
                    )
                    SolventaTopBar(title = "Con volver", showBack = true, onBack = { clicks += 1 })
                    SolventaTopBar(title = "Sin volver", showBack = false, onBack = {})
                    SolventaSelect(
                        label = "Tipo",
                        value = choice.value,
                        options = listOf("CC", "CE"),
                        expanded = expanded.value,
                        onExpandedChange = { expanded.value = it },
                        onSelect = { choice.value = it },
                    )
                    SolventaSwitch("Aviso", checked = checked.value, onCheckedChange = { checked.value = it })
                    SolventaSwitch("Oculto", checked = false, onCheckedChange = {}, showLabel = false)
                    SolventaTextField(
                        value = field.value,
                        onValueChange = { field.value = it },
                        label = "Placa",
                        helper = "",
                        style = SolventaFieldStyle.Filled,
                        state = SolventaFieldState.ReadOnly,
                        testTag = "field_filled",
                    )
                    SolventaTextField(
                        value = "valor",
                        onValueChange = {},
                        label = "Nota",
                        helper = "ayuda",
                        state = SolventaFieldState.Default,
                        visualTransformation = PasswordVisualTransformation(),
                        testTag = "field_default",
                    )
                    SolventaBottomSheet(visible = false, onDismiss = {}) {}
                    SolventaBottomSheet(visible = sheet.value, onDismiss = { sheet.value = false }) {
                        Text("Hoja")
                    }
                }
            }
        }

        rule.onNodeWithText("claro").assertIsDisplayed()
        rule.onNodeWithTag("tab_Polizas").performClick()
        rule.onNodeWithText("Lleno").performClick()
        rule.onNodeWithText("Tonal").performClick()
        rule.onNodeWithText("Texto").performClick()
        rule.onNodeWithText("Filtro").performClick()
        rule.onNodeWithTag("solventa_status_success").assertIsDisplayed()
        rule.onNodeWithTag("solventa_status_error").assertIsDisplayed()
        rule.onNodeWithTag("solventa_status_processing").assertIsDisplayed()
        rule.onNodeWithTag("solventa_banner_info").assertIsDisplayed()
        rule.onNodeWithTag("solventa_banner_error").assertIsDisplayed()
        rule.onNodeWithTag("solventa_floating_action").performClick()
        rule.onNodeWithTag("solventa_icon_button").performClick()
        rule.onNodeWithTag("icon_on_surface").performClick()
        rule.onNodeWithTag("action_volver").performClick()
        rule.onNodeWithTag("top_bar_root").assertIsDisplayed()
        rule.onNodeWithText("Tipo: CC").performClick()
        rule.waitForIdle()
        rule.onNodeWithText("CE").performClick()
        rule.onAllNodesWithTag("solventa_switch")[0].performClick()
        rule.onNodeWithTag("solventa_bottom_sheet").assertIsDisplayed()
        assertEquals(Destination.Polizas, selected.value)
        assertEquals("CE", choice.value)
        assertEquals(true, chip.value)
        assertEquals(true, checked.value)
        assertEquals(7, clicks)
        assertEquals(4.dp, SolventaSpacing.s4)
        assertEquals(12.dp, SolventaSpacing.s12)
        assertEquals(20.dp, SolventaSpacing.s20)
        assertEquals(24.dp, SolventaSpacing.s24)
        assertEquals(32.dp, SolventaSpacing.s32)
        assertEquals(40.dp, SolventaSpacing.s40)
        assertEquals(64.dp, SolventaSpacing.s64)
    }

    @Test
    fun givenTheIdentityMark_whenTopBarShows_thenTheMarkStaysAndBackStillWorks() {
        var backs = 0
        rule.setContent {
            SolventaTheme {
                SolventaTopBar(
                    title = "Oferta",
                    showBack = true,
                    onBack = { backs += 1 },
                    modifier = Modifier,
                    titleStyle = MaterialTheme.typography.titleMedium,
                    minHeight = 48.dp,
                    showIdentityMark = true,
                )
            }
        }
        rule.onNodeWithTag("mortgage_identity_mark").assertIsDisplayed()
        rule.onNodeWithTag("mortgage_identity_mark").assertHasNoClickAction()
        rule.onNodeWithTag("action_volver").performClick()
        assertEquals(1, backs)
    }

    @Test
    fun givenAPhotoStub_whenConsumed_thenItIsCleared() {
        OnboardingPhotoInjector.next = byteArrayOf(1)
        OnboardingPhotoInjector.captureUri = null
        assertEquals(1, OnboardingPhotoInjector.consume()!!.size)
        assertNull(OnboardingPhotoInjector.consume())
        assertNull(OnboardingPhotoInjector.captureUri)
    }
}
