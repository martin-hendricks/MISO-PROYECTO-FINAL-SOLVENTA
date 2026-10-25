package com.grupo8_uniandes.solventa.login

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import com.grupo8_uniandes.solventa.ui.login.LoginFailure
import com.grupo8_uniandes.solventa.ui.login.LoginScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class LoginScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenOpened_whenRead_thenCopyIsEmptyAndPasswordIsMasked() {
        var email = ""
        var password = ""
        var ingresar = 0
        rule.setContent {
            SolventaTheme {
                LoginScreen(
                    email = email,
                    password = password,
                    failure = LoginFailure.None,
                    onEmail = { email = it },
                    onPassword = { password = it },
                    onIngresar = { ingresar += 1 },
                    onBack = {},
                    onCreateAccount = {},
                    onBiometric = {},
                    modifier = Modifier,
                )
            }
        }

        rule.onNodeWithTag("screen_login").assertIsDisplayed()
        rule.onNodeWithTag("top_bar_back").assertIsDisplayed()
        rule.onNodeWithText("Solventa").assertIsDisplayed()
        rule.onNodeWithText("Ingresa a tus seguros").assertIsDisplayed()
        rule.onNodeWithText("Tus pólizas, tus avisos de siniestro y tus pagos automáticos, en un solo lugar.").assertIsDisplayed()
        rule.onNodeWithText("Correo electrónico").assertIsDisplayed()
        rule.onNodeWithText("Contraseña").assertIsDisplayed()
        rule.onNodeWithText("Ingresar").assertIsDisplayed()
        rule.onNodeWithText("Crear cuenta").assertIsDisplayed()
        rule.onNodeWithTag("action_ingresar").assertIsEnabled()
        rule.onAllNodesWithText("camila@correo.com").assertCountEquals(0)
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onAllNodesWithTag("solventa_banner_error").assertCountEquals(0)
        rule.onNodeWithTag("field_login_contrasena").performTextInput("secret")
        rule.onNode(
            hasTestTag("field_login_contrasena") and
                SemanticsMatcher.keyIsDefined(SemanticsProperties.Password),
        ).assertExists()
        rule.onNodeWithTag("action_ingresar").performClick()
        assertEquals("secret", password)
        assertEquals(1, ingresar)
    }

    @Test
    fun givenRejected_whenShown_thenBannerAndPasswordHint() {
        rule.setContent {
            SolventaTheme {
                LoginScreen(
                    email = "camila@correo.com",
                    password = "wrong",
                    failure = LoginFailure.Rejected,
                    onEmail = {},
                    onPassword = {},
                    onIngresar = {},
                    onBack = {},
                    onCreateAccount = {},
                    onBiometric = {},
                )
            }
        }

        rule.onNodeWithText("Correo o contraseña incorrectos. Reintenta en esta vista.").assertIsDisplayed()
        rule.onAllNodesWithText("Revisa tu contraseña").assertCountEquals(1)
        rule.onNodeWithText("No se pudo completar el ingreso. Reintenta en esta vista.").assertDoesNotExist()
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
    }

    @Test
    fun givenIncomplete_whenShown_thenNoBannerAndNoHint() {
        rule.setContent {
            SolventaTheme {
                LoginScreen(
                    email = "",
                    password = "secret",
                    failure = LoginFailure.None,
                    onEmail = {},
                    onPassword = {},
                    onIngresar = {},
                    onBack = {},
                    onCreateAccount = {},
                    onBiometric = {},
                )
            }
        }

        rule.onAllNodesWithTag("solventa_banner_error").assertCountEquals(0)
        rule.onAllNodesWithText("Revisa tu contraseña").assertCountEquals(0)
    }

    @Test
    fun givenUnavailable_whenShown_thenConnectionBannerOnly() {
        var password by mutableStateOf("secret")
        rule.setContent {
            SolventaTheme {
                LoginScreen(
                    email = "camila@correo.com",
                    password = password,
                    failure = LoginFailure.Unavailable,
                    onEmail = {},
                    onPassword = { password = it },
                    onIngresar = {},
                    onBack = {},
                    onCreateAccount = {},
                    onBiometric = {},
                )
            }
        }

        rule.onNodeWithText("No se pudo completar el ingreso. Reintenta en esta vista.").assertIsDisplayed()
        rule.onNodeWithText("Correo o contraseña incorrectos. Reintenta en esta vista.").assertDoesNotExist()
        rule.onAllNodesWithText("Revisa tu contraseña").assertCountEquals(0)
        rule.onNode(
            hasTestTag("field_login_contrasena") and
                SemanticsMatcher.keyIsDefined(SemanticsProperties.Password),
        ).assertExists()
    }

    @Test
    fun givenPasswordAndBiometric_whenToggledAndRetried_thenPasswordShowsAndCallbackRuns() {
        var password by mutableStateOf("")
        var biometric = 0
        var signedIn = 0
        rule.setContent {
            SolventaTheme {
                LoginScreen(
                    email = "",
                    password = password,
                    failure = LoginFailure.None,
                    onEmail = {},
                    onPassword = { password = it },
                    onIngresar = { signedIn += 1 },
                    onBack = {},
                    onCreateAccount = {},
                    onBiometric = { biometric += 1 },
                    biometricEnabled = true,
                )
            }
        }

        rule.onNodeWithText("Entra con huella o rostro").assertIsDisplayed()
        rule.onNodeWithText(
            "Android pide la biometría del dispositivo. Si falla, usa correo y contraseña.",
        ).assertIsDisplayed()
        rule.onNodeWithText("Usar biometría").assertIsDisplayed()
        rule.onNodeWithText("Ingresar").assertIsDisplayed()
        rule.onNodeWithText("Crear cuenta").assertIsDisplayed()
        rule.onNodeWithTag("field_login_contrasena").performTextInput("secret")
        rule.onNode(
            hasTestTag("field_login_contrasena") and
                SemanticsMatcher.keyIsDefined(SemanticsProperties.Password),
        ).assertExists()
        assertEquals("••••••", rule.onNodeWithTag("field_login_contrasena").shownText())
        rule.onNodeWithTag("toggle_login_contrasena").performClick()
        rule.onNodeWithContentDescription("Ocultar contraseña").assertIsDisplayed()
        assertEquals("secret", rule.onNodeWithTag("field_login_contrasena").shownText())
        rule.onNodeWithTag("action_biometric").performClick()
        rule.onNodeWithTag("action_ingresar").performScrollTo().performClick()
        assertEquals(1, biometric)
        assertEquals(1, signedIn)
        assertEquals("secret", password)
    }

    @Test
    fun givenBiometricFallback_whenShown_thenPasswordEntryReplacesThePrompt() {
        rule.setContent {
            SolventaTheme {
                LoginScreen(
                    email = "camila@correo.com",
                    password = "secret",
                    failure = LoginFailure.Rejected,
                    onEmail = {},
                    onPassword = {},
                    onIngresar = {},
                    onBack = {},
                    onCreateAccount = {},
                    onBiometric = {},
                    biometricEnabled = true,
                    biometricFallback = true,
                )
            }
        }

        rule.onNodeWithText("La biometría no estuvo disponible").assertIsDisplayed()
        rule.onNodeWithText(
            "Entra con correo y contraseña para no quedar fuera de tus pólizas.",
        ).assertIsDisplayed()
        rule.onNodeWithText("Ingresar").assertIsDisplayed()
        rule.onNodeWithText("Correo o contraseña incorrectos. Reintenta en esta vista.").assertIsDisplayed()
        rule.onAllNodesWithTag("action_biometric").assertCountEquals(0)
        rule.onAllNodesWithText("Usar biometría").assertCountEquals(0)
    }

    @Test
    fun givenConfirm_whenAcceptedOrDeclined_thenTheChoiceIsReported() {
        var accepted = 0
        var declined = 0
        rule.setContent {
            SolventaTheme {
                LoginScreen(
                    email = "camila@correo.com",
                    password = "secret",
                    failure = LoginFailure.None,
                    onEmail = {},
                    onPassword = {},
                    onIngresar = {},
                    onBack = {},
                    onCreateAccount = {},
                    onBiometric = {},
                    confirmBiometric = true,
                    onAcceptBiometric = { accepted += 1 },
                    onDeclineBiometric = { declined += 1 },
                )
            }
        }

        rule.onNodeWithText("¿Quieres ingresar con huella o rostro la próxima vez?").assertIsDisplayed()
        rule.onAllNodesWithTag("action_biometric").assertCountEquals(0)
        rule.onNodeWithText("Ahora no").performClick()
        assertEquals(1, declined)
        assertEquals(0, accepted)
    }

    @Test
    fun givenSignedOut_whenShown_thenBackIsHidden() {
        rule.setContent {
            SolventaTheme {
                LoginScreen(
                    email = "",
                    password = "",
                    failure = LoginFailure.None,
                    onEmail = {},
                    onPassword = {},
                    onIngresar = {},
                    onBack = {},
                    showBack = false,
                    onCreateAccount = {},
                    onBiometric = {},
                )
            }
        }

        rule.onNodeWithTag("top_bar_root").assertIsDisplayed()
        rule.onAllNodesWithTag("action_volver").assertCountEquals(0)
    }
}

private fun androidx.compose.ui.test.SemanticsNodeInteraction.shownText(): String =
    fetchSemanticsNode().config[SemanticsProperties.EditableText].text
