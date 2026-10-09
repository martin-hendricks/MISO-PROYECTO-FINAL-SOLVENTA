package com.grupo8_uniandes.solventa.consent

import android.content.Context
import android.content.Intent
import android.view.KeyEvent
import androidx.test.platform.app.InstrumentationRegistry
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertIsOff
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.test.click
import androidx.compose.ui.test.isDialog
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.data.consent.ConsentPrefsFile
import com.grupo8_uniandes.solventa.data.consent.KeyConsentRecords
import com.grupo8_uniandes.solventa.data.consent.SharedPrefsConsentRepository
import com.grupo8_uniandes.solventa.data.region.KeyAppliedRegion
import com.grupo8_uniandes.solventa.data.region.KeyFirstLaunchCompleted
import com.grupo8_uniandes.solventa.data.region.RegionPrefsFile
import com.grupo8_uniandes.solventa.data.registration.SharedPrefsRegistrationRepository
import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.ui.registration.OnboardingPhotoInjector
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ConsentTest {
    @get:Rule
    val rule = createAndroidComposeRule<MainActivity>()

    @Before
    fun resetStores() {
        clearConsentStores()
        OnboardingPhotoInjector.next = null
        rule.activityRule.scenario.recreate()
    }

    @After
    fun clearInjector() {
        OnboardingPhotoInjector.next = null
    }

    @Test
    fun givenValidAccount_whenContinuar_thenAltaStartsOffAndGrantOpensHome() {
        openAccount()
        fillAccount()
        OnboardingPhotoInjector.next = byteArrayOf(1, 2, 3)
        rule.onNodeWithTag("action_foto").performScrollTo().performClick()
        rule.onNodeWithTag("action_continuar").performScrollTo().performClick()
        rule.waitForTag("screen_consentimiento")
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_splash").assertCountEquals(0)
        rule.onNodeWithTag("solventa_switch").assertIsOff()
        rule.onNodeWithTag("action_aceptar_continuar").assertIsNotEnabled()
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
        rule.onNodeWithText("Consentimiento").assertIsDisplayed()
        rule.onNodeWithText("Tratamiento de datos").assertIsDisplayed()
        rule.onNodeWithText(
            "Autorizas el tratamiento de tus datos para emitir y administrar tu póliza (habeas data).",
        ).assertIsDisplayed()

        rule.onNodeWithTag("solventa_switch").performClick()
        rule.onNodeWithTag("action_aceptar_continuar").performClick()
        rule.waitForTag("screen_inicio")
        rule.onNodeWithTag("bottom_bar").assertIsDisplayed()
        val records = consentRecords()
        assertTrue(records.orEmpty().startsWith("GRANT|"))
        assertEquals(1, records.orEmpty().lines().size)
    }

    @Test
    fun givenAltaSwitchOn_whenBack_thenAccountAndNoConsentLine() {
        openAccount()
        fillAccount()
        OnboardingPhotoInjector.next = byteArrayOf(4)
        rule.onNodeWithTag("action_foto").performScrollTo().performClick()
        rule.onNodeWithTag("action_continuar").performScrollTo().performClick()
        rule.waitForTag("screen_consentimiento")
        rule.onNodeWithTag("solventa_switch").performClick()
        rule.onNodeWithTag("action_volver").performClick()
        rule.waitForTag("screen_onboarding")
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
        assertEquals(null, consentRecords())
    }

    @Test
    fun givenEachRegion_whenAltaShows_thenCopyStaysSpanish() {
        listOf("es-CO", "es-MX", "es-CL", "es-PE").forEach { tag ->
            val context = ApplicationProvider.getApplicationContext<Context>()
            context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE)
                .edit()
                .putString(KeyAppliedRegion, tag)
                .putBoolean(KeyFirstLaunchCompleted, true)
                .commit()
            saveRegistration()
            context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
            rule.activityRule.scenario.recreate()
            rule.waitForTag("screen_consentimiento")
            rule.onNodeWithText("Tratamiento de datos").assertIsDisplayed()
            rule.onNodeWithText(
                "Autorizas el tratamiento de tus datos para emitir y administrar tu póliza (habeas data).",
            ).assertIsDisplayed()
        }
    }

    private fun openAccount() {
        rule.waitForTag("screen_idioma_region")
        rule.onNodeWithTag("action_continuar").performClick()
        rule.waitForTag("screen_onboarding")
    }

    private fun fillAccount() {
        rule.onNodeWithTag("field_nombre").performTextInput("Camila")
        rule.onNodeWithTag("field_apellidos").performTextInput("Restrepo")
        rule.onNodeWithTag("field_correo").performTextInput("camila@correo.com")
        rule.onNodeWithTag("field_tipo").performTextInput("CC")
        rule.onNodeWithTag("field_numero").performTextInput("1023456789")
        rule.onNodeWithTag("field_contrasena").performTextInput("secret")
    }
}

@RunWith(AndroidJUnit4::class)
class ConsentProfileTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    @Before
    fun seedAccount() {
        clearConsentStores()
        val context = ApplicationProvider.getApplicationContext<Context>()
        context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE)
            .edit()
            .putString(KeyAppliedRegion, "es-CO")
            .putBoolean(KeyFirstLaunchCompleted, true)
            .commit()
        saveRegistration()
    }

    @Test
    fun givenGrant_whenProfileSheet_thenCloseKeepsOtorgadoAndRevokeStaysSignedIn() {
        ChangeDataTreatment(SharedPrefsConsentRepository(appContext())) { 10L }.grant()
        launchProfile().use {
            rule.waitForTag("screen_perfil")
            rule.onNodeWithTag("profile_entry").assertIsDisplayed()
            rule.onNodeWithTag("profile_consent").assertIsDisplayed()
            rule.onNodeWithText("otorgado").assertIsDisplayed()
            rule.onNodeWithTag("profile_consent").performClick()
            rule.onNodeWithTag("solventa_bottom_sheet").assertIsDisplayed()
            rule.onNodeWithTag("action_close").performClick()
            rule.onNodeWithText("otorgado").assertIsDisplayed()
            rule.onNodeWithTag("profile_consent").performClick()
            rule.onNodeWithTag("solventa_switch").performClick()
            rule.onNodeWithTag("action_aceptar_continuar").performClick()
            rule.onNodeWithText("revocado").assertIsDisplayed()
            rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
            rule.onAllNodesWithTag("screen_consentimiento").assertCountEquals(0)
        }
    }

    @Test
    fun givenNoGrant_whenProfile_thenConsentRowIsAbsent() {
        launchProfile().use {
            rule.waitForTag("screen_perfil")
            rule.onNodeWithTag("profile_entry").assertIsDisplayed()
            rule.onAllNodesWithTag("profile_consent").assertCountEquals(0)
            rule.onAllNodesWithText("Consentimiento de perfilado").assertCountEquals(0)
            rule.onAllNodesWithTag("screen_consentimiento").assertCountEquals(0)
        }
    }

    @Test
    fun givenGrant_whenScrimOrSystemBack_thenOtorgadoStays() {
        ChangeDataTreatment(SharedPrefsConsentRepository(appContext())) { 10L }.grant()
        launchProfile().use {
            rule.waitForTag("profile_consent")
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
            InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
            rule.waitUntil(timeoutMillis = 8_000) {
                rule.onAllNodesWithTag("solventa_bottom_sheet").fetchSemanticsNodes().isEmpty()
            }
            rule.onNodeWithText("otorgado").assertIsDisplayed()
            rule.onAllNodesWithTag("screen_consentimiento").assertCountEquals(0)
        }
    }

    @Test
    fun givenRevoked_whenRelaunched_thenInicioNotAlta() {
        val repository = SharedPrefsConsentRepository(appContext())
        ChangeDataTreatment(repository) { 10L }.grant()
        ChangeDataTreatment(repository) { 11L }.revoke()
        val intent = Intent(appContext(), MainActivity::class.java)
            .putExtra(MainActivity.EXTRA_SPLASH_HOLD_MILLIS, 0L)
        ActivityScenario.launch<MainActivity>(intent).use {
            rule.waitForTag("screen_inicio")
            rule.onAllNodesWithTag("screen_consentimiento").assertCountEquals(0)
            assertEquals(ConsentState.Revoked, repository.read().state)
        }
    }

    @Test
    fun givenRevoked_whenGrantFromSheet_thenOtorgadoWithoutAlta() {
        val repository = SharedPrefsConsentRepository(appContext())
        ChangeDataTreatment(repository) { 10L }.grant()
        ChangeDataTreatment(repository) { 11L }.revoke()
        launchProfile().use {
            rule.waitForTag("profile_consent")
            rule.onNodeWithText("revocado").assertIsDisplayed()
            rule.onNodeWithTag("profile_consent").performClick()
            rule.onNodeWithTag("solventa_switch").performClick()
            rule.onNodeWithTag("action_aceptar_continuar").performClick()
            rule.onNodeWithText("otorgado").assertIsDisplayed()
            rule.onAllNodesWithTag("screen_consentimiento").assertCountEquals(0)
        }
    }

    private fun launchProfile(): ActivityScenario<MainActivity> {
        val intent = Intent(appContext(), MainActivity::class.java)
            .putExtra(MainActivity.EXTRA_SPLASH_HOLD_MILLIS, 0L)
            .putExtra(MainActivity.EXTRA_RESUME_PROFILE, true)
        return ActivityScenario.launch(intent)
    }
}

private fun appContext(): Context = ApplicationProvider.getApplicationContext()

private fun clearConsentStores() {
    val context = appContext()
    context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    context.getSharedPreferences("registration_prefs", Context.MODE_PRIVATE).edit().clear().commit()
    context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    java.io.File(context.filesDir, "registration/document.jpg").delete()
}

private fun saveRegistration() {
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

private fun consentRecords(): String? {
    return appContext().getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE)
        .getString(KeyConsentRecords, null)
}

private fun ComposeTestRule.waitForTag(tag: String) {
    waitUntil(timeoutMillis = 8_000) {
        onAllNodesWithTag(tag).fetchSemanticsNodes().isNotEmpty()
    }
}
