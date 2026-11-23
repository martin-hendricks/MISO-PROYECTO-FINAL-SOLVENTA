package com.grupo8_uniandes.solventa.accessibility

import androidx.activity.ComponentActivity
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.assertHeightIsAtLeast
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.ui.consent.ConsentScreen
import com.grupo8_uniandes.solventa.ui.login.LoginFailure
import com.grupo8_uniandes.solventa.ui.login.LoginScreen
import com.grupo8_uniandes.solventa.ui.registration.LivenessCameraContent
import com.grupo8_uniandes.solventa.ui.registration.LivenessPhase
import com.grupo8_uniandes.solventa.ui.registration.LivenessScreen
import com.grupo8_uniandes.solventa.ui.registration.LivenessUiState
import com.grupo8_uniandes.solventa.ui.registration.OnboardingScreen
import com.grupo8_uniandes.solventa.ui.registration.OnboardingUiState
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h4000dp")
class FirstRunSemanticsTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenOnboarding_whenShown_thenTitleIsHeadingAndClicksAreNamed() {
        rule.setContent {
            SolventaTheme {
                OnboardingScreen(
                    state = OnboardingUiState(),
                    onGivenName = {},
                    onSurnames = {},
                    onEmail = {},
                    onDocumentType = {},
                    onDocumentNumber = {},
                    onPassword = {},
                    onPasswordConfirm = {},
                    onPhotoAttached = {},
                    onPhotoDeclined = {},
                    onHabeasData = {},
                    onContinue = {},
                    onExistingAccount = {},
                )
            }
        }
        rule.onNodeWithText("Crea tu cuenta").performScrollTo()
        rule.onNode(isHeading() and androidx.compose.ui.test.hasText("Crea tu cuenta")).assertExists()
        assertClicksNamed()
    }

    @Test
    fun givenLiveness_whenShown_thenTitleIsHeading() {
        rule.setContent {
            SolventaTheme {
                LivenessScreen(
                    state = LivenessUiState(),
                    onGivenName = {},
                    onSurnames = {},
                    onEmail = {},
                    onDocumentType = {},
                    onDocumentNumber = {},
                    onPassword = {},
                    onContinue = {},
                    onExistingAccount = {},
                )
            }
        }
        rule.onNode(isHeading() and androidx.compose.ui.test.hasText("Prueba de vida")).assertExists()
    }

    @Test
    fun givenLivenessCamera_whenShown_thenTheShutterIsNamedAndAtLeast48dp() {
        rule.setContent {
            SolventaTheme {
                LivenessCameraContent(
                    state = LivenessUiState(phase = LivenessPhase.Camera),
                    onShutter = {},
                    onRepeat = {},
                    onRetry = {},
                    onContinue = {},
                    onContinueWithDocument = {},
                    onExistingAccount = {},
                    preview = {},
                )
            }
        }
        rule.onNode(isHeading() and androidx.compose.ui.test.hasText("Prueba de vida")).assertExists()
        rule.onNodeWithTag("action_liveness_shutter").assertHeightIsAtLeast(48.dp)
        assertClicksNamed()
    }

    @Test
    fun givenConsent_whenShown_thenTitleIsHeading() {
        rule.setContent {
            SolventaTheme {
                ConsentScreen(
                    switchOn = false,
                    confirmEnabled = false,
                    onSwitch = {},
                    onConfirm = {},
                    onBack = {},
                )
            }
        }
        rule.onNode(isHeading() and androidx.compose.ui.test.hasText("Tratamiento de datos")).assertExists()
    }

    @Test
    fun givenLogin_whenShown_thenTitleIsHeading() {
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
                    onCreateAccount = {},
                    onBiometric = {},
                )
            }
        }
        rule.onNode(isHeading() and androidx.compose.ui.test.hasText("Ingresa a tus seguros")).assertExists()
    }

    private fun assertClicksNamed() {
        rule.onAllNodes(hasClickAction()).fetchSemanticsNodes().forEach { node ->
            val text = node.config.getOrElse(SemanticsProperties.Text) { emptyList() }
            val description = node.config.getOrElse(SemanticsProperties.ContentDescription) { emptyList() }
            val editable = node.config.contains(SemanticsProperties.EditableText)
            assertTrue(
                "unnamed click at ${node.boundsInRoot} config=${node.config}",
                text.isNotEmpty() || description.isNotEmpty() || editable,
            )
        }
    }
}
