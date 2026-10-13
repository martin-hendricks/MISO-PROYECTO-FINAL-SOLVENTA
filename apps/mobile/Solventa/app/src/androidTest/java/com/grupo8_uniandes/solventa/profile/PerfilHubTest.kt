package com.grupo8_uniandes.solventa.profile

import android.content.Intent
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.grupo8_uniandes.solventa.MainActivity
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PerfilHubTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    private lateinit var scenario: ActivityScenario<MainActivity>

    @Before
    fun openSignedInShell() {
        val intent = Intent(ApplicationProvider.getApplicationContext(), MainActivity::class.java)
            .putExtra(MainActivity.EXTRA_ENTER_SIGNED_IN_SHELL, true)
        scenario = ActivityScenario.launch(intent)
        rule.waitUntil(timeoutMillis = 5_000) {
            rule.onAllNodesWithTag("bottom_bar").fetchSemanticsNodes().isNotEmpty()
        }
        rule.onNodeWithTag("tab_Perfil").performClick()
        rule.waitUntil(timeoutMillis = 5_000) {
            rule.onAllNodesWithTag("screen_perfil").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @After
    fun close() {
        scenario.close()
    }

    @Test
    fun givenPerfil_whenSignOutIsCancelled_thenTheBarStays() {
        rule.onNodeWithTag("action_sign_out").performClick()
        rule.onNodeWithTag("action_sign_out_cancel").performClick()
        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
        rule.onNodeWithTag("bottom_bar").assertIsDisplayed()
    }

    @Test
    fun givenPerfil_whenSignOutIsConfirmed_thenLoginHasNoBar() {
        rule.onNodeWithTag("action_sign_out").performClick()
        rule.onNodeWithTag("action_sign_out_confirm").performClick()
        rule.waitUntil(timeoutMillis = 8_000) {
            rule.onAllNodesWithTag("screen_login").fetchSemanticsNodes().isNotEmpty()
        }
        rule.onNodeWithTag("screen_login").assertIsDisplayed()
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
    }
}
