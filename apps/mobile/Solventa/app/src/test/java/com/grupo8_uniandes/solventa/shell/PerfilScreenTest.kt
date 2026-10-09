package com.grupo8_uniandes.solventa.shell

import android.content.Context
import androidx.activity.ComponentActivity
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.click
import androidx.compose.ui.test.isDialog
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.test.performTouchInput
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.data.region.KeyAppliedRegion
import com.grupo8_uniandes.solventa.data.region.RegionPrefsFile
import com.grupo8_uniandes.solventa.ui.shell.PerfilScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class PerfilScreenTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    private val context = ApplicationProvider.getApplicationContext<Context>()

    @Before
    fun clearPrefs() {
        context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    }

    @Test
    fun givenProfile_whenListo_thenAppliedRegionIsStored() {
        rule.setContent {
            SolventaTheme {
                PerfilScreen()
            }
        }

        rule.onNodeWithText("Idioma y región").performClick()
        rule.onNodeWithTag("solventa_bottom_sheet").assertIsDisplayed()
        rule.onNodeWithText("Español · México").performClick()
        rule.onNodeWithTag("action_listo").performSemanticsAction(SemanticsActions.OnClick)

        assertEquals("es-MX", appliedTag())
        assertTrue(rule.activity.intent.getBooleanExtra(MainActivity.EXTRA_RESUME_PROFILE, false))
    }

    @Test
    fun givenProfile_whenSheetDismissed_thenAppliedRegionStaysColombia() {
        rule.setContent {
            SolventaTheme {
                PerfilScreen()
            }
        }

        rule.onNodeWithText("Idioma y región").performClick()
        rule.onNodeWithText("Español · Chile").performClick()
        rule.onNode(isDialog()).performTouchInput {
            click(Offset(width / 2f, 24f))
        }
        rule.waitUntil(timeoutMillis = 8_000) {
            rule.onAllNodesWithTag("solventa_bottom_sheet").fetchSemanticsNodes().isEmpty()
        }

        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
        rule.onAllNodesWithTag("solventa_bottom_sheet").assertCountEquals(0)
        assertEquals("es-CO", appliedTag())
    }

    @Test
    fun givenProfile_whenRowStagedWithoutListo_thenAppliedRegionStaysColombia() {
        rule.setContent {
            SolventaTheme {
                PerfilScreen()
            }
        }

        rule.onNodeWithText("Idioma y región").performClick()
        rule.onNodeWithText("Español · Chile").performClick()
        rule.onNodeWithTag("solventa_bottom_sheet").assertIsDisplayed()

        assertEquals("es-CO", appliedTag())
    }

    private fun appliedTag(): String? =
        context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE)
            .getString(KeyAppliedRegion, null)
}
