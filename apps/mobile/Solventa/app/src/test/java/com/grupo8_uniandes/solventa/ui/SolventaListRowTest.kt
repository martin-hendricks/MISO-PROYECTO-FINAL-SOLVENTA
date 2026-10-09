package com.grupo8_uniandes.solventa.ui

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.ui.components.SolventaListRow
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class SolventaListRowTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenNoClick_whenShown_thenRowStays() {
        rule.setContent {
            SolventaTheme {
                SolventaListRow(label = "Idioma y región", testTag = "profile_entry")
            }
        }

        rule.onNodeWithTag("profile_entry").assertExists()
    }

    @Test
    fun givenClick_whenTapped_thenCallbackRuns() {
        var clicks = 0
        rule.setContent {
            SolventaTheme {
                SolventaListRow(
                    label = "Idioma y región",
                    testTag = "profile_entry",
                    onClick = { clicks += 1 },
                )
            }
        }

        rule.onNodeWithTag("profile_entry").performClick()
        rule.onAllNodesWithTag("profile_entry").assertCountEquals(1)
        assertEquals(1, clicks)
    }
}
