package com.grupo8_uniandes.solventa.region

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.click
import androidx.compose.ui.test.isDialog
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTouchInput
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.data.region.KeyAppliedRegion
import com.grupo8_uniandes.solventa.data.region.RegionPrefsFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class IdiomaRegionTest {
    @get:Rule
    val rule = createAndroidComposeRule<MainActivity>()

    @Before
    fun resetRegion() {
        clearRegionPrefs()
        rule.activityRule.scenario.recreate()
    }

    @Test
    fun givenFirstLaunch_whenSplashFinishes_thenFourRegionsAndColombiaSelected() {
        rule.waitForTag("screen_idioma_region")
        listOf(
            "Español · Colombia",
            "Español · México",
            "Español · Chile",
            "Español · Perú",
        ).forEach { name ->
            rule.onNodeWithText(name).assertIsDisplayed()
        }
        rule.onNodeWithText("Paso 1 de 3 · Elige país e idioma").assertIsDisplayed()
        rule.onNodeWithTag("region_es_CO").assertIsSelected()
        rule.onNodeWithTag("region_check", useUnmergedTree = true).assertIsDisplayed()
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        assertFalse(requestedPermissions().contains(Manifest.permission.READ_MEDIA_IMAGES))
        assertFalse(requestedPermissions().contains(Manifest.permission.READ_EXTERNAL_STORAGE))
        assertFalse(requestedPermissions().contains(Manifest.permission.ACCESS_FINE_LOCATION))
        assertFalse(requestedPermissions().contains(Manifest.permission.ACCESS_COARSE_LOCATION))
    }

    @Test
    fun givenMexicoRow_whenShown_thenSampleAmountAndDate() {
        rule.waitForTag("screen_idioma_region")
        rule.onNodeWithText("es-MX · MXN · 09/07/2026 · $1,234.56").assertIsDisplayed()
    }

    @Test
    fun givenPicker_whenContinuar_thenOnboardingWithoutPermissions() {
        rule.waitForTag("screen_idioma_region")
        rule.onNodeWithTag("action_continuar").performClick()
        rule.waitForTag("screen_onboarding")
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_idioma_region").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
    }

    @Test
    fun givenRowTapped_whenProcessRestartsBeforeContinuar_thenDraftReturns() {
        rule.waitForTag("screen_idioma_region")
        rule.onNodeWithText("Español · México").performClick()
        rule.activityRule.scenario.recreate()
        rule.waitForTag("screen_idioma_region")
        rule.onNodeWithTag("region_es_MX").assertIsSelected()
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
    }

    @Test
    fun givenContinuar_whenRelaunched_thenPickerStaysClosed() {
        rule.waitForTag("screen_idioma_region")
        rule.onNodeWithTag("action_continuar").performClick()
        rule.waitForTag("screen_onboarding")
        rule.activityRule.scenario.recreate()
        rule.waitForTag("screen_onboarding")
        rule.onAllNodesWithTag("screen_idioma_region").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
    }

    @Test
    fun givenPicker_whenShown_thenBackControlIsAbsent() {
        rule.waitForTag("screen_idioma_region")
        rule.onAllNodesWithTag("idioma_back").assertCountEquals(0)
        rule.onNodeWithTag("screen_idioma_region").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
    }
}

@RunWith(AndroidJUnit4::class)
class IdiomaRegionProfileTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    @Test
    fun givenProfile_whenListo_thenSheetClosesOnProfile() {
        clearRegionPrefs()
        val intent = Intent(ApplicationProvider.getApplicationContext(), MainActivity::class.java)
            .putExtra(MainActivity.EXTRA_ENTER_SIGNED_IN_SHELL, true)
        ActivityScenario.launch<MainActivity>(intent).use { scenario ->
            rule.waitForTag("bottom_bar")
            rule.onNodeWithText("Perfil").performClick()
            rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
            rule.onNodeWithText("Idioma y región").performClick()
            rule.onNodeWithTag("solventa_bottom_sheet").assertIsDisplayed()
            rule.onAllNodesWithText("Paso 1 de 3 · Elige país e idioma").assertCountEquals(0)
            rule.onAllNodesWithTag("action_continuar").assertCountEquals(0)
            rule.onNodeWithTag("tab_Perfil").assertIsSelected()
            rule.onNodeWithText("Español · México").performClick()
            rule.onNodeWithTag("action_listo").performClick()
            rule.waitUntil(timeoutMillis = 8_000) {
                appliedTag() == "es-MX" &&
                    rule.onAllNodesWithTag("screen_perfil").fetchSemanticsNodes().isNotEmpty() &&
                    rule.onAllNodesWithTag("solventa_bottom_sheet").fetchSemanticsNodes().isEmpty()
            }
            rule.onAllNodesWithTag("screen_onboarding").assertCountEquals(0)
            scenario.recreate()
            rule.waitForTag("bottom_bar")
            assertEquals("es-MX", appliedTag())
        }
    }

    @Test
    fun givenProfile_whenDismissed_thenAppliedRegionStays() {
        clearRegionPrefs()
        val intent = Intent(ApplicationProvider.getApplicationContext(), MainActivity::class.java)
            .putExtra(MainActivity.EXTRA_ENTER_SIGNED_IN_SHELL, true)
        ActivityScenario.launch<MainActivity>(intent).use { scenario ->
            rule.waitForTag("bottom_bar")
            rule.onNodeWithText("Perfil").performClick()
            rule.onNodeWithText("Idioma y región").performClick()
            rule.onNodeWithTag("solventa_bottom_sheet").assertIsDisplayed()
            rule.onNodeWithText("Español · Chile").performClick()
            rule.onNode(isDialog()).performTouchInput {
                click(Offset(width / 2f, 24f))
            }
            rule.waitUntil(timeoutMillis = 8_000) {
                rule.onAllNodesWithTag("solventa_bottom_sheet").fetchSemanticsNodes().isEmpty()
            }
            rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
            rule.onAllNodesWithTag("solventa_bottom_sheet").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_onboarding").assertCountEquals(0)
            assertEquals("es-CO", appliedTag())
        }
    }
}

private fun clearRegionPrefs() {
    val context = ApplicationProvider.getApplicationContext<Context>()
    context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
}

private fun appliedTag(): String? {
    val context = ApplicationProvider.getApplicationContext<Context>()
    return context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE)
        .getString(KeyAppliedRegion, null)
}

private fun requestedPermissions(): Set<String> {
    val context = ApplicationProvider.getApplicationContext<Context>()
    @Suppress("DEPRECATION")
    val info = context.packageManager.getPackageInfo(
        context.packageName,
        PackageManager.GET_PERMISSIONS,
    )
    return info.requestedPermissions?.toSet().orEmpty()
}

private fun ComposeTestRule.waitForTag(tag: String) {
    waitUntil(timeoutMillis = 8_000) {
        onAllNodesWithTag(tag).fetchSemanticsNodes().isNotEmpty()
    }
}
