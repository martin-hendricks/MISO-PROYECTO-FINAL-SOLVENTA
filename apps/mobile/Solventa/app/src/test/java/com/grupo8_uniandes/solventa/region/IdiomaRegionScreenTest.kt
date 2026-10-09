package com.grupo8_uniandes.solventa.region

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class IdiomaRegionScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenColombia_whenShown_thenFourRowsAndNoBackControl() {
        var draft by mutableStateOf(Region.Colombia)
        var continued = 0
        rule.setContent {
            SolventaTheme {
                IdiomaRegionScreen(
                    draft = draft,
                    onSelect = { draft = it },
                    onContinue = { continued += 1 },
                )
            }
        }

        rule.onNodeWithText("Idioma y región").assertIsDisplayed()
        rule.onNodeWithText("Paso 1 de 3 · Elige país e idioma").assertIsDisplayed()
        rule.onNodeWithTag("region_es_CO").assertIsSelected()
        rule.onNodeWithTag("region_check", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithText("Español · México").performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("Español · Chile").performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("Español · Perú").performScrollTo().assertIsDisplayed()
        rule.onAllNodesWithTag("idioma_back").assertCountEquals(0)

        rule.onNodeWithText("Español · México").performScrollTo().performClick()
        rule.onNodeWithTag("region_es_MX").assertIsSelected()
        rule.onNodeWithTag("action_continuar").performClick()
        assertEquals(Region.Mexico, draft)
        assertEquals(1, continued)
    }
}
