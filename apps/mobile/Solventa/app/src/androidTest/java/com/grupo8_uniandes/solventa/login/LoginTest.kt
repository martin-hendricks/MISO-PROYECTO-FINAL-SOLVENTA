package com.grupo8_uniandes.solventa.login

import android.content.Context
import android.content.Intent
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.performTextReplacement
import androidx.compose.ui.text.AnnotatedString
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.data.consent.ConsentPrefsFile
import com.grupo8_uniandes.solventa.data.region.KeyAppliedRegion
import com.grupo8_uniandes.solventa.data.region.KeyFirstLaunchCompleted
import com.grupo8_uniandes.solventa.data.region.RegionPrefsFile
import com.grupo8_uniandes.solventa.data.registration.RegistrationPrefsFile
import com.grupo8_uniandes.solventa.data.registration.SharedPrefsRegistrationRepository
import com.grupo8_uniandes.solventa.domain.registration.Registration
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class LoginTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    @Before
    fun clearStores() {
        clearLoginStores()
    }

    @Test
    fun givenAccountForm_whenYaTengoCuenta_thenEmptyLoginWithoutBar() {
        readyForAccount("es-CO")
        ActivityScenario.launch<MainActivity>(splashIntent()).use {
            rule.waitForTag("screen_onboarding")
            rule.onNodeWithTag("action_ya_tengo_cuenta").performScrollTo().performClick()
            rule.waitForTag("screen_login")
            rule.onNodeWithText("Ingresa a tus seguros").assertIsDisplayed()
            rule.onNodeWithText("Tus pólizas, tus avisos de siniestro y tus pagos automáticos, en un solo lugar.").assertIsDisplayed()
            rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
            assertFalse(registrationCompleted())
            assertFalse(consentRecorded())
        }
    }

    @Test
    fun givenSavedPair_whenIngresar_thenHomeWithoutConsentOrPhoto() {
        saveAccount()
        ActivityScenario.launch<MainActivity>(onboardingIntent()).use {
            rule.openLogin()
            rule.typePair("camila@correo.com", "secret")
            rule.onNodeWithTag("action_ingresar").performScrollTo().performClick()
            rule.waitForTag("screen_inicio")
            rule.onNodeWithTag("bottom_bar").assertIsDisplayed()
            rule.onAllNodesWithTag("screen_consentimiento").assertCountEquals(0)
            rule.onAllNodesWithTag("action_foto").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
            assertFalse(consentRecorded())
        }
    }

    @Test
    fun givenWrongPair_whenIngresar_thenBannerStaysUntilAMatch() {
        saveAccount()
        ActivityScenario.launch<MainActivity>(onboardingIntent()).use {
            rule.openLogin()
            rule.typePair("camila@correo.com", "other")
            rule.onNodeWithTag("action_ingresar").performScrollTo().performClick()
            rule.onNodeWithText("Correo o contraseña incorrectos. Reintenta en esta vista.").assertIsDisplayed()
            rule.onNodeWithText("Revisa tu contraseña").assertIsDisplayed()
            rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
            rule.assertValue("field_login_correo", "camila@correo.com")
            rule.onNodeWithTag("field_login_contrasena").performTextReplacement("secret")
            rule.onNodeWithTag("action_ingresar").performScrollTo().performClick()
            rule.waitForTag("screen_inicio")
            rule.onNodeWithTag("bottom_bar").assertIsDisplayed()
        }
    }

    @Test
    fun givenBlank_whenIngresar_thenNoCredentialCopy() {
        readyForAccount("es-CO")
        ActivityScenario.launch<MainActivity>(splashIntent()).use {
            rule.waitForTag("screen_onboarding")
            rule.onNodeWithTag("action_ya_tengo_cuenta").performScrollTo().performClick()
            rule.waitForTag("screen_login")
            rule.onNodeWithTag("action_ingresar").performScrollTo().performClick()
            rule.onAllNodesWithTag("solventa_banner_error").assertCountEquals(0)
            rule.onAllNodesWithText("Revisa tu contraseña").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
        }
    }

    @Test
    fun givenLoginFromAccount_whenBackOrCrearCuenta_thenAccountDraftRemains() {
        readyForAccount("es-CO")
        ActivityScenario.launch<MainActivity>(splashIntent()).use {
            rule.waitForTag("screen_onboarding")
            rule.onNodeWithTag("field_nombre").performTextInput("Camila")
            rule.onNodeWithTag("action_ya_tengo_cuenta").performScrollTo().performClick()
            rule.waitForTag("screen_login")
            rule.onNodeWithTag("field_login_correo").performTextInput("camila@correo.com")
            rule.onNodeWithTag("action_crear_cuenta").performScrollTo().performClick()
            rule.waitForTag("screen_onboarding")
            rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
            rule.assertValue("field_nombre", "Camila")
            assertFalse(registrationCompleted())
            rule.onNodeWithTag("action_ya_tengo_cuenta").performScrollTo().performClick()
            rule.waitForTag("screen_login")
            rule.onNodeWithTag("action_volver").performClick()
            rule.waitForTag("screen_onboarding")
            rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
            rule.assertValue("field_nombre", "Camila")
        }
    }

    @Test
    fun givenExistingAccountSplash_whenBackAndCrearCuenta_thenSplashDoesNotReplay() {
        ActivityScenario.launch<MainActivity>(existingAccountIntent()).use {
            rule.waitForTag("screen_login")
            rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
            rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
            rule.onNodeWithTag("action_volver").performClick()
            rule.onNodeWithTag("screen_login").assertIsDisplayed()
            rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
            rule.onNodeWithTag("action_crear_cuenta").performScrollTo().performClick()
            rule.waitForTag("screen_onboarding")
            rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
        }
    }

    @Test
    fun givenEachLocale_whenLoginShows_thenSpanishCopy() {
        listOf("es-CO", "es-MX", "es-CL", "es-PE").forEach { tag ->
            readyForAccount(tag)
            ActivityScenario.launch<MainActivity>(splashIntent()).use {
                rule.waitForTag("screen_onboarding")
                rule.onNodeWithTag("action_ya_tengo_cuenta").performScrollTo().performClick()
                rule.waitForTag("screen_login")
                rule.onNodeWithText("Ingresa a tus seguros").assertIsDisplayed()
                rule.onNodeWithText("Tus pólizas, tus avisos de siniestro y tus pagos automáticos, en un solo lugar.").assertIsDisplayed()
                rule.onNodeWithText("Correo electrónico").assertIsDisplayed()
                rule.onNodeWithText("Contraseña").assertIsDisplayed()
                rule.onNodeWithText("Ingresar").assertIsDisplayed()
                rule.onNodeWithText("Crear cuenta").assertIsDisplayed()
            }
        }
    }
}

private fun appContext(): Context = ApplicationProvider.getApplicationContext()

private fun splashIntent(): Intent =
    Intent(appContext(), MainActivity::class.java)
        .putExtra(MainActivity.EXTRA_SPLASH_HOLD_MILLIS, 0L)

private fun onboardingIntent(): Intent =
    splashIntent().putExtra(MainActivity.EXTRA_OPEN_ONBOARDING, true)

private fun existingAccountIntent(): Intent =
    splashIntent().putExtra(MainActivity.EXTRA_EXISTING_ACCOUNT, true)

private fun clearLoginStores() {
    val context = appContext()
    context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    context.getSharedPreferences(RegistrationPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    File(context.filesDir, "registration/document.jpg").delete()
}

private fun readyForAccount(tag: String) {
    clearLoginStores()
    appContext().getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE)
        .edit()
        .putString(KeyAppliedRegion, tag)
        .putBoolean(KeyFirstLaunchCompleted, true)
        .commit()
}

private fun saveAccount() {
    SharedPrefsRegistrationRepository(appContext()).save(
        Registration(
            givenName = "Camila",
            surnames = "Restrepo",
            email = "camila@correo.com",
            documentType = "CC",
            documentNumber = "1023456789",
            password = "secret",
            documentPhoto = byteArrayOf(1),
        ),
    )
}

private fun registrationCompleted(): Boolean {
    return appContext().getSharedPreferences(RegistrationPrefsFile, Context.MODE_PRIVATE)
        .getBoolean("registration_completed", false)
}

private fun consentRecorded(): Boolean {
    val prefs = appContext().getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE)
    return prefs.contains("records") || prefs.contains("state")
}

private fun ComposeTestRule.openLogin() {
    waitForTag("screen_onboarding")
    onNodeWithTag("action_ya_tengo_cuenta").performScrollTo().performClick()
    waitForTag("screen_login")
}

private fun ComposeTestRule.typePair(email: String, password: String) {
    onNodeWithTag("field_login_correo").performTextInput(email)
    onNodeWithTag("field_login_contrasena").performTextInput(password)
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
