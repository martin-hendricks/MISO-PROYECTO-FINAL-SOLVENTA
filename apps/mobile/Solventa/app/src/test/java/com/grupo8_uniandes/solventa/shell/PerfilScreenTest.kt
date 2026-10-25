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
import androidx.compose.ui.test.assertHasNoClickAction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.click
import androidx.compose.ui.test.isDialog
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.test.performTouchInput
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.data.consent.ConsentPrefsFile
import com.grupo8_uniandes.solventa.data.consent.SharedPrefsConsentRepository
import com.grupo8_uniandes.solventa.data.profile.SessionPrefsFile
import com.grupo8_uniandes.solventa.data.region.KeyAppliedRegion
import com.grupo8_uniandes.solventa.data.region.RegionPrefsFile
import com.grupo8_uniandes.solventa.data.registration.RegistrationPrefsFile
import com.grupo8_uniandes.solventa.data.registration.SharedPrefsRegistrationRepository
import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.domain.profile.DevicePermissionReader
import com.grupo8_uniandes.solventa.domain.profile.PermissionKind
import com.grupo8_uniandes.solventa.domain.profile.PermissionRow
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.ui.shell.PerfilScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowDialog
import java.util.Locale

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
        context.getSharedPreferences(RegistrationPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
        context.getSharedPreferences(SessionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
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

    @Test
    fun givenRegistration_whenHubOpens_thenIdentityAndRowsAreShown() {
        SharedPrefsRegistrationRepository(context).save(sampleRegistration())
        ChangeDataTreatment(SharedPrefsConsentRepository(context)) { 1L }.grant()
        rule.setContent {
            SolventaTheme {
                PerfilScreen(
                    permissionReader = publishedPermissions(),
                )
            }
        }

        rule.onNodeWithTag("profile_identity").assertIsDisplayed().assertHasNoClickAction()
        rule.onNodeWithText("Camila Restrepo").assertIsDisplayed()
        rule.onNodeWithText("CC 1.023.456.789").assertIsDisplayed()
        rule.onNodeWithTag("profile_entry").assertIsDisplayed()
        rule.onNodeWithText("Español · Colombia · es-CO · COP").assertIsDisplayed()
        rule.onNodeWithTag("profile_location").assertIsDisplayed()
        rule.onNodeWithTag("profile_camera").assertIsDisplayed()
        rule.onNodeWithTag("profile_photos").assertIsDisplayed()
        rule.onNodeWithTag("profile_consent").assertIsDisplayed()
        rule.onNodeWithTag("action_sign_out").assertIsDisplayed()
        rule.onAllNodesWithText("Permitida · mientras usas la app").assertCountEquals(2)
        rule.onNodeWithText("Permitidas · una imagen del aviso").assertIsDisplayed()
        rule.onAllNodesWithText("Perfil").assertCountEquals(0)
        rule.onAllNodesWithText("Nueva cotización").assertCountEquals(0)
        rule.onAllNodesWithText("Renovar").assertCountEquals(0)
        rule.onAllNodesWithText("Modificar").assertCountEquals(0)
        rule.onAllNodesWithText("Cancelar").assertCountEquals(0)
        rule.onAllNodesWithText("Sin originación activa").assertCountEquals(0)
        rule.onAllNodesWithTag("profile_profiling").assertCountEquals(0)
    }

    @Test
    fun givenUnpublishedPermission_whenHubOpens_thenAllowedSentenceIsAbsent() {
        rule.setContent {
            SolventaTheme {
                PerfilScreen()
            }
        }

        rule.onNodeWithTag("profile_location").assertIsDisplayed()
        rule.onNodeWithTag("profile_camera").assertIsDisplayed()
        rule.onNodeWithTag("profile_photos").assertIsDisplayed()
        rule.onAllNodesWithText("Permitida · mientras usas la app").assertCountEquals(0)
        rule.onAllNodesWithText("Permitidas · una imagen del aviso").assertCountEquals(0)
        rule.onNodeWithTag("profile_location").performClick()
        rule.onNodeWithTag("sheet_permission").assertIsDisplayed()
        rule.onNodeWithTag("action_close").performClick()
        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
    }

    @Test
    fun givenSignOutSheet_whenCancelled_thenHubStays() {
        var signedOut = 0
        rule.setContent {
            SolventaTheme {
                PerfilScreen(onSignedOut = { signedOut += 1 })
            }
        }

        rule.onNodeWithTag("action_sign_out").performClick()
        rule.onNodeWithTag("sheet_sign_out").assertIsDisplayed()
        rule.onNodeWithText("Tendrás que volver a ingresar para ver tus pólizas.").assertIsDisplayed()
        rule.onNodeWithTag("action_sign_out_confirm").assertIsDisplayed()
        rule.onNodeWithTag("action_sign_out_cancel").performClick()
        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
        rule.onAllNodesWithTag("sheet_sign_out").assertCountEquals(0)
        assertEquals(0, signedOut)
    }

    @Test
    fun givenSignOutSheet_whenConfirmed_thenSignedOutOnce() {
        var signedOut = 0
        rule.setContent {
            SolventaTheme {
                PerfilScreen(onSignedOut = { signedOut += 1 })
            }
        }

        rule.onNodeWithTag("action_sign_out").performClick()
        rule.onNodeWithTag("action_sign_out_confirm").performClick()
        rule.waitUntil(timeoutMillis = 8_000) { signedOut == 1 }
        assertEquals(1, signedOut)
    }

    @Test
    fun givenOrigination_whenProfilingOpens_thenConsentStays() {
        ChangeDataTreatment(SharedPrefsConsentRepository(context)) { 1L }.grant()
        rule.setContent {
            SolventaTheme {
                PerfilScreen(originationActive = true)
            }
        }

        rule.onNodeWithTag("profile_profiling").assertIsDisplayed()
        rule.onNodeWithText("otorgado").assertIsDisplayed()
        rule.onNodeWithTag("profile_profiling").performClick()
        rule.onNodeWithTag("sheet_profiling").assertIsDisplayed()
        rule.onNodeWithTag("action_close").performClick()
        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
        rule.onNodeWithText("otorgado").assertIsDisplayed()
    }

    @Test
    fun givenFourRegions_whenSignOutCopyIsRead_thenItStaysSpanish() {
        listOf("es-CO", "es-MX", "es-CL", "es-PE").map(Locale::forLanguageTag).forEach { locale ->
            val config = android.content.res.Configuration(context.resources.configuration)
            config.setLocale(locale)
            val resources = context.createConfigurationContext(config).resources
            assertEquals("Cerrar sesión", resources.getString(com.grupo8_uniandes.solventa.R.string.action_sign_out))
            assertEquals(
                "Tendrás que volver a ingresar para ver tus pólizas.",
                resources.getString(com.grupo8_uniandes.solventa.R.string.sign_out_body),
            )
        }
    }

    @Test
    fun givenProfile_whenBiometricToggled_thenPreferenceIsStored() {
        val registration = SharedPrefsRegistrationRepository(context)
        rule.setContent {
            SolventaTheme {
                PerfilScreen()
            }
        }

        rule.onNodeWithTag("profile_biometric").assertIsDisplayed()
        rule.onNodeWithText("Ingresa con huella o rostro").assertIsDisplayed()
        assertFalse(registration.biometricUnlockEnabled())
        rule.onNodeWithTag("profile_biometric_switch").performClick()
        assertTrue(registration.biometricUnlockEnabled())
        rule.onNodeWithTag("profile_biometric_switch").performClick()
        assertFalse(registration.biometricUnlockEnabled())
    }

    private fun sampleRegistration() = Registration(
        givenName = "Camila",
        surnames = "Restrepo",
        email = "camila@example.com",
        documentType = "CC",
        documentNumber = "1.023.456.789",
        password = "secret",
        documentPhoto = byteArrayOf(1),
    )

    private fun publishedPermissions() = DevicePermissionReader {
        PermissionKind.entries.map { PermissionRow(it, published = true) }
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
        context.getSharedPreferences(RegistrationPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
        context.getSharedPreferences(SessionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
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
