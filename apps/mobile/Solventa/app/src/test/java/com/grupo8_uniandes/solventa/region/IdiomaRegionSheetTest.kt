package com.grupo8_uniandes.solventa.region

import androidx.compose.ui.Modifier
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performSemanticsAction
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionSheet
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class IdiomaRegionSheetTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenHidden_whenNotOpened_thenSheetIsAbsent() {
        rule.setContent {
            SolventaTheme {
                IdiomaRegionSheet(
                    visible = false,
                    draft = Region.Colombia,
                    onSelect = {},
                    onListo = {},
                    onDismiss = {},
                    modifier = Modifier,
                )
            }
        }

        rule.onAllNodesWithTag("solventa_bottom_sheet").assertCountEquals(0)
        rule.onAllNodesWithTag("action_listo").assertCountEquals(0)
    }

    @Test
    fun givenOpen_whenRowAndListo_thenCallbacksFireWithoutSignupHeading() {
        var draft by mutableStateOf(Region.Colombia)
        var listed = 0
        rule.setContent {
            SolventaTheme {
                IdiomaRegionSheet(
                    visible = true,
                    draft = draft,
                    onSelect = { draft = it },
                    onListo = { listed += 1 },
                    onDismiss = {},
                )
            }
        }

        rule.onNodeWithTag("solventa_bottom_sheet").assertIsDisplayed()
        rule.onAllNodesWithText("Paso 1 de 3 · Elige país e idioma").assertCountEquals(0)
        rule.onAllNodesWithTag("action_continuar").assertCountEquals(0)
        rule.onNodeWithText("Español · Chile").performClick()
        rule.onNodeWithTag("action_listo").performSemanticsAction(SemanticsActions.OnClick)
        assertEquals(Region.Chile, draft)
        assertEquals(1, listed)
    }
}
