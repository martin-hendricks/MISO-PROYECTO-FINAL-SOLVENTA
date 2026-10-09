package com.grupo8_uniandes.solventa.registration

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.isDialog
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.text.AnnotatedString
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.data.consent.ConsentPrefsFile
import com.grupo8_uniandes.solventa.data.region.KeyAppliedRegion
import com.grupo8_uniandes.solventa.data.region.KeyFirstLaunchCompleted
import com.grupo8_uniandes.solventa.data.region.RegionPrefsFile
import com.grupo8_uniandes.solventa.data.registration.KeyRegistrationCompleted
import com.grupo8_uniandes.solventa.data.registration.RegistrationPrefsFile
import com.grupo8_uniandes.solventa.ui.registration.OnboardingPhotoInjector
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class OnboardingTest {
    @get:Rule
    val rule = createAndroidComposeRule<MainActivity>()

    @Before
    fun resetStores() {
        clearRegionPrefs()
        clearRegistration()
        clearConsent()
        OnboardingPhotoInjector.next = null
        rule.activityRule.scenario.recreate()
    }

    @After
    fun clearInjector() {
        OnboardingPhotoInjector.next = null
    }

    @Test
    fun givenRegionContinuar_whenAccountOpens_thenEmptyFormWithoutPermissionPrompt() {
        openAccount()
        rule.onNodeWithText("Crea tu cuenta").assertIsDisplayed()
        rule.onNodeWithText("1 de 2 · Cuenta").assertIsDisplayed()
        rule.onAllNodesWithText("Foto de una sola cara, sin flash.").assertCountEquals(2)
        listOf(
            "field_nombre",
            "field_apellidos",
            "field_correo",
            "field_tipo",
            "field_numero",
            "field_contrasena",
        ).forEach { tag ->
            rule.assertValue(tag, "")
        }
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
        rule.onAllNodes(isDialog()).assertCountEquals(0)
        assertFalse(declaredPermissions().contains(Manifest.permission.READ_MEDIA_IMAGES))
        assertFalse(declaredPermissions().contains(Manifest.permission.READ_EXTERNAL_STORAGE))
        assertFalse(declaredPermissions().contains(Manifest.permission.ACCESS_FINE_LOCATION))
        assertFalse(declaredPermissions().contains(Manifest.permission.ACCESS_COARSE_LOCATION))
    }

    @Test
    fun givenInvalidEmail_whenContinuar_thenFieldIsMarkedAndValuesStay() {
        openAccount()
        fill(
            email = "camila",
        )
        rule.onNodeWithText("El correo no es válido.").performScrollTo().assertIsDisplayed()
        rule.assertValue("field_nombre", "Camila")
        rule.assertValue("field_apellidos", "Restrepo")
        rule.onNodeWithTag("action_continuar").assertIsNotEnabled()
        rule.onNodeWithTag("screen_onboarding").assertIsDisplayed()
    }

    @Test
    fun givenValidFormAndPhoto_whenContinuar_thenConsent() {
        openAccount()
        fill(email = "camila@correo.com")
        OnboardingPhotoInjector.next = byteArrayOf(1, 2, 3)
        rule.onNodeWithTag("action_foto").performScrollTo().performClick()
        rule.onNodeWithTag("action_continuar").performScrollTo().assertIsEnabled()
        rule.onNodeWithTag("action_continuar").performClick()
        rule.waitForTag("screen_consentimiento")
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_login").assertCountEquals(0)
        assertEquals(true, registrationCompleted())
    }

    @Test
    fun givenPhotoDeclined_whenReturned_thenFormStaysAndContinuarStaysDisabled() {
        openAccount()
        fill(email = "camila@correo.com")
        OnboardingPhotoInjector.next = byteArrayOf()
        rule.onNodeWithTag("action_foto").performScrollTo().performClick()
        rule.onNodeWithTag("screen_onboarding").assertIsDisplayed()
        rule.assertValue("field_nombre", "Camila")
        rule.onNodeWithTag("action_continuar").assertIsNotEnabled()
    }

    @Test
    fun givenPartialForm_whenYaTengoCuenta_thenLoginWithoutRegistration() {
        openAccount()
        rule.onNodeWithTag("field_correo").performTextInput("camila@correo.com")
        rule.onNodeWithTag("action_ya_tengo_cuenta").performScrollTo().performClick()
        rule.waitForTag("screen_login")
        rule.onNodeWithText("Login").assertIsDisplayed()
        rule.onAllNodesWithTag("field_correo").assertCountEquals(0)
        rule.onAllNodesWithTag("field_contrasena").assertCountEquals(0)
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_consentimiento").assertCountEquals(0)
        assertEquals(false, registrationCompleted())
        assertEquals(false, consentRecorded())
    }

    @Test
    fun givenEachRegion_whenAccountShows_thenCopyStaysSpanish() {
        listOf("es-CO", "es-MX", "es-CL", "es-PE").forEach { tag ->
            confirmRegion(tag)
            rule.activityRule.scenario.recreate()
            rule.waitForTag("screen_onboarding")
            rule.onNodeWithText("Crea tu cuenta").assertIsDisplayed()
            rule.onNodeWithText("1 de 2 · Cuenta").assertIsDisplayed()
            rule.onAllNodesWithText("Foto de una sola cara, sin flash.").assertCountEquals(2)
        }
    }

    private fun openAccount() {
        rule.waitForTag("screen_idioma_region")
        rule.onNodeWithTag("action_continuar").performClick()
        rule.waitForTag("screen_onboarding")
    }

    private fun fill(email: String) {
        rule.onNodeWithTag("field_nombre").performTextInput("Camila")
        rule.onNodeWithTag("field_apellidos").performTextInput("Restrepo")
        rule.onNodeWithTag("field_correo").performTextInput(email)
        rule.onNodeWithTag("field_tipo").performTextInput("CC")
        rule.onNodeWithTag("field_numero").performTextInput("1023456789")
        rule.onNodeWithTag("field_contrasena").performTextInput("secret")
    }

    private fun confirmRegion(tag: String) {
        val context = ApplicationProvider.getApplicationContext<Context>()
        context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE)
            .edit()
            .putString(KeyAppliedRegion, tag)
            .putBoolean(KeyFirstLaunchCompleted, true)
            .commit()
        clearRegistration()
    }
}

@RunWith(AndroidJUnit4::class)
class OnboardingExistingAccountTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    @Test
    fun givenExistingAccount_whenStartupFinishes_thenInicioWithoutLoginPlaceholder() {
        val intent = Intent(ApplicationProvider.getApplicationContext(), MainActivity::class.java)
            .putExtra(MainActivity.EXTRA_SPLASH_HOLD_MILLIS, 0L)
            .putExtra(MainActivity.EXTRA_EXISTING_ACCOUNT, true)
        ActivityScenario.launch<MainActivity>(intent).use {
            rule.waitForTag("screen_inicio")
            rule.onAllNodesWithTag("screen_login").assertCountEquals(0)
        }
    }
}

private fun clearRegionPrefs() {
    val context = ApplicationProvider.getApplicationContext<Context>()
    context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
}

private fun clearRegistration() {
    val context = ApplicationProvider.getApplicationContext<Context>()
    context.getSharedPreferences(RegistrationPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    File(context.filesDir, "registration/document.jpg").delete()
}

private fun clearConsent() {
    val context = ApplicationProvider.getApplicationContext<Context>()
    context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
}

private fun consentRecorded(): Boolean {
    val context = ApplicationProvider.getApplicationContext<Context>()
    val prefs = context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE)
    return prefs.contains("records") || prefs.contains("state")
}

private fun registrationCompleted(): Boolean {
    val context = ApplicationProvider.getApplicationContext<Context>()
    return context.getSharedPreferences(RegistrationPrefsFile, Context.MODE_PRIVATE)
        .getBoolean(KeyRegistrationCompleted, false)
}

private fun declaredPermissions(): Set<String> {
    val context = ApplicationProvider.getApplicationContext<Context>()
    @Suppress("DEPRECATION")
    val info = context.packageManager.getPackageInfo(
        context.packageName,
        PackageManager.GET_PERMISSIONS,
    )
    return info.requestedPermissions?.toSet().orEmpty()
}

private fun ComposeTestRule.assertValue(tag: String, expected: String) {
    val actual = onNodeWithTag(tag).fetchSemanticsNode().config.getOrNull(SemanticsProperties.EditableText)
    assertEquals(AnnotatedString(expected), actual)
}

private fun ComposeTestRule.waitForTag(tag: String) {
    waitUntil(timeoutMillis = 8_000) {
        onAllNodesWithTag(tag).fetchSemanticsNodes().isNotEmpty()
    }
}
