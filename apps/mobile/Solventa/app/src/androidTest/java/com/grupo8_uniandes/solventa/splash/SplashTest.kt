package com.grupo8_uniandes.solventa.splash

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.grupo8_uniandes.solventa.MainActivity
import org.junit.Assert.assertFalse
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SplashVisibleTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    @Test
    fun givenColdStart_whenAppOpens_thenWordmarkWithoutNavigationBar() {
        ActivityScenario.launch<MainActivity>(splashIntent(holdMillis = 30_000L)).use {
            rule.onNodeWithTag("screen_splash").assertIsDisplayed()
            rule.onNodeWithText("Solventa").assertIsDisplayed()
            rule.onNodeWithText("Aseguradora digital").assertIsDisplayed()
            rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
            rule.onAllNodesWithTag("top_bar_root").assertCountEquals(0)
            rule.onAllNodesWithTag("top_bar_back").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_idioma_region").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_login").assertCountEquals(0)
        }
    }
}

@RunWith(AndroidJUnit4::class)
class SplashFirstUseTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    @Test
    fun givenFirstUse_whenStartupFinishes_thenIdiomaRegion() {
        clearRegionPrefs()
        ActivityScenario.launch<MainActivity>(splashIntent(holdMillis = 0L)).use {
            rule.waitForTag("screen_idioma_region")
            rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
            rule.onNodeWithTag("screen_idioma_region").assertIsDisplayed()
            rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_login").assertCountEquals(0)
        }
    }
}

@RunWith(AndroidJUnit4::class)
class SplashExistingAccountTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    @Test
    fun givenExistingAccount_whenStartupFinishes_thenInicio() {
        val intent = splashIntent(holdMillis = 0L)
            .putExtra(MainActivity.EXTRA_EXISTING_ACCOUNT, true)
        ActivityScenario.launch<MainActivity>(intent).use {
            rule.waitForTag("screen_inicio")
            rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
            rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
            rule.onNodeWithTag("bottom_bar").assertIsDisplayed()
            rule.onNodeWithTag("tab_Inicio").assertIsSelected()
            rule.onAllNodesWithTag("screen_idioma_region").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_login").assertCountEquals(0)
        }
    }
}

@RunWith(AndroidJUnit4::class)
class SplashPermissionTest {
    @get:Rule
    val rule = createAndroidComposeRule<MainActivity>()

    @Test
    fun givenInstall_whenPackageInspected_thenNoCameraPhotosOrGps() {
        val context = rule.activity
        @Suppress("DEPRECATION")
        val info = context.packageManager.getPackageInfo(
            context.packageName,
            PackageManager.GET_PERMISSIONS,
        )
        val requested = info.requestedPermissions?.toSet().orEmpty()
        listOf(
            Manifest.permission.CAMERA,
            Manifest.permission.READ_MEDIA_IMAGES,
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
        ).forEach { permission ->
            assertFalse(requested.contains(permission))
        }
    }
}

private fun splashIntent(holdMillis: Long): Intent =
    Intent(ApplicationProvider.getApplicationContext(), MainActivity::class.java)
        .putExtra(MainActivity.EXTRA_SPLASH_HOLD_MILLIS, holdMillis)

private fun clearRegionPrefs() {
    val context = ApplicationProvider.getApplicationContext<Context>()
    context.getSharedPreferences("region_prefs", Context.MODE_PRIVATE).edit().clear().commit()
}

private fun ComposeTestRule.waitForTag(tag: String) {
    waitUntil(timeoutMillis = 5_000) {
        onAllNodesWithTag(tag).fetchSemanticsNodes().isNotEmpty()
    }
}
