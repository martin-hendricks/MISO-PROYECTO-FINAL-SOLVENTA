package com.grupo8_uniandes.solventa.claim

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenProviderCatalog
import com.grupo8_uniandes.solventa.domain.bff.claim.ProviderCatalog
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.shell.SiniestrosScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test

class MapaPrestadoresTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenLocationAllowed_whenTheCatalogOpens_thenTheStubRowsAreVisible() {
        val rows = (OpenProviderCatalog().open(locationAllowed = true) as ProviderCatalog.Open).rows
        rule.setContent {
            SolventaTheme {
                MapaPrestadoresScreen(rows = rows, onOpenAssistance = {})
            }
        }

        rule.onNodeWithText("Taller Norte").assertIsDisplayed()
        rule.onNodeWithText("A 1,2 km · Chapinero").assertIsDisplayed()
        rule.onNodeWithText("Taller Sur").assertIsDisplayed()
        rule.onNodeWithText("A 3,4 km · Kennedy").assertIsDisplayed()
        rule.onNodeWithText("SIN-P01").assertIsDisplayed()
        rule.onNodeWithTag("screen_mapa_prestadores").assertIsDisplayed()
    }

    @Test
    fun givenTheClaimsList_whenShown_thenTheCatalogChevronIsAbsent() {
        rule.setContent {
            SolventaTheme {
                SiniestrosScreen(claims = emptyList(), onOpenClaim = {})
            }
        }

        rule.onNodeWithTag("screen_siniestros").assertIsDisplayed()
        rule.onAllNodesWithTag("action_open_catalog").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_mapa_prestadores").assertCountEquals(0)
    }
}
