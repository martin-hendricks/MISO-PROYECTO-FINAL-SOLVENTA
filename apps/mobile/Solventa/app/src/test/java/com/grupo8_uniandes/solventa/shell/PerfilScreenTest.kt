package com.grupo8_uniandes.solventa.shell

import android.content.Context
import androidx.activity.ComponentActivity
import androidx.activity.ComponentDialog
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.click
import androidx.compose.ui.test.isDialog
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.test.performTouchInput
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.data.consent.ConsentPrefsFile
import com.grupo8_uniandes.solventa.data.consent.SharedPrefsConsentRepository
import com.grupo8_uniandes.solventa.data.region.KeyAppliedRegion
import com.grupo8_uniandes.solventa.data.region.RegionPrefsFile
import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
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
import org.robolectric.shadows.ShadowDialog

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class PerfilScreenTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    private val context = ApplicationProvider.getApplicationContext<Context>()

    @Before
    fun clearPrefs() {
        context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
        context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    }

    @Test
    fun givenProfile_whenListo_thenAppliedRegionIsStored() {
        rule.setContent {
            SolventaTheme {
                PerfilScreen()
            }
        }

        rule.onAllNodesWithTag("profile_consent").assertCountEquals(0)
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
                PerfilScreen(modifier = Modifier)
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

    @Test
    fun givenGrant_whenRevokedFromSheet_thenHubShowsRevocado() {
        ChangeDataTreatment(SharedPrefsConsentRepository(context)) { 1L }.grant()
        rule.setContent {
            SolventaTheme {
                PerfilScreen()
            }
        }

        rule.onNodeWithTag("profile_entry").assertIsDisplayed()
        rule.onNodeWithTag("profile_consent").assertIsDisplayed()
        rule.onNodeWithText("otorgado").assertIsDisplayed()
        rule.onNodeWithTag("profile_consent").performClick()
        rule.onNodeWithTag("action_close").performClick()
        rule.onNodeWithText("otorgado").assertIsDisplayed()
        rule.onNodeWithTag("profile_consent").performClick()
        rule.onNodeWithTag("solventa_switch").performClick()
        rule.onNodeWithTag("action_aceptar_continuar").performClick()
        rule.onNodeWithText("revocado").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_consentimiento").assertCountEquals(0)

        rule.onNodeWithTag("profile_consent").performClick()
        rule.onNodeWithTag("solventa_switch").performClick()
        rule.onNodeWithTag("action_aceptar_continuar").performClick()
        rule.onNodeWithText("otorgado").assertIsDisplayed()
    }

    @Test
    fun givenGrant_whenScrimOrBack_thenHubStaysOtorgado() {
        ChangeDataTreatment(SharedPrefsConsentRepository(context)) { 1L }.grant()
        rule.setContent {
            SolventaTheme {
                PerfilScreen()
            }
        }

        rule.onNodeWithTag("profile_consent").performClick()
        rule.onNodeWithTag("solventa_switch").performClick()
        rule.onNode(isDialog()).performTouchInput {
            click(Offset(width / 2f, 24f))
        }
        rule.waitUntil(timeoutMillis = 8_000) {
            rule.onAllNodesWithTag("solventa_bottom_sheet").fetchSemanticsNodes().isEmpty()
        }
        rule.onNodeWithText("otorgado").assertIsDisplayed()

        rule.onNodeWithTag("profile_consent").performClick()
        rule.onNodeWithTag("solventa_switch").performClick()
        (ShadowDialog.getLatestDialog() as ComponentDialog)
            .onBackPressedDispatcher
            .onBackPressed()
        rule.waitUntil(timeoutMillis = 8_000) {
            rule.onAllNodesWithTag("solventa_bottom_sheet").fetchSemanticsNodes().isEmpty()
        }
        rule.onNodeWithText("otorgado").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_consentimiento").assertCountEquals(0)
    }

    private fun appliedTag(): String? =
        context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE)
            .getString(KeyAppliedRegion, null)
}

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class PerfilScreenWithoutActivityTest {
    @get:Rule
    val rule = createComposeRule()

    private val context = ApplicationProvider.getApplicationContext<Context>()

    @Before
    fun clearPrefs() {
        context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
        context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    }

    @Test
    fun givenNoActivity_whenListo_thenAppliedRegionIsStored() {
        rule.setContent {
            SolventaTheme {
                CompositionLocalProvider(LocalContext provides context) {
                    PerfilScreen()
                }
            }
        }

        rule.onNodeWithText("Idioma y región").performClick()
        rule.onNodeWithText("Español · México").performClick()
        rule.onNodeWithTag("action_listo").performSemanticsAction(SemanticsActions.OnClick)

        assertEquals(
            "es-MX",
            context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE)
                .getString(KeyAppliedRegion, null),
        )
    }
}
