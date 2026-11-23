package com.grupo8_uniandes.solventa.accessibility

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performScrollTo
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.login.LoginFailure
import com.grupo8_uniandes.solventa.ui.login.LoginScreen
import com.grupo8_uniandes.solventa.ui.registration.OnboardingScreen
import com.grupo8_uniandes.solventa.ui.registration.OnboardingUiState
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h4000dp")
class LargeFontScaleTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenLargestText_whenScreensShow_thenTitlesStayReadable() {
        rule.setContent {
            AccessibleTheme(fontScale = 2f) {
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
        rule.onNodeWithText("Crea tu cuenta").performScrollTo().assertIsDisplayed()
    }

    @Test
    fun givenLargestText_whenLoginAndHomeShow_thenTitlesStayReadable() {
        rule.setContent {
            AccessibleTheme(fontScale = 2f) {
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
        rule.onNodeWithText("Ingresa a tus seguros").performScrollTo().assertIsDisplayed()
    }

    @Test
    fun givenLargestText_whenHomeAndFieldShow_thenValueStaysReadable() {
        rule.setContent {
            AccessibleTheme(fontScale = 2f) {
                androidx.compose.foundation.layout.Column {
                    SolventaTextField(
                        value = "1234567",
                        onValueChange = {},
                        label = "Prima",
                        helper = "Como aparece en tu documento",
                        externalLabel = true,
                        style = SolventaFieldStyle.Outlined,
                    )
                }
            }
        }
        rule.onNodeWithText("1234567").assertIsDisplayed()
        rule.onNodeWithText("Como aparece en tu documento").assertIsDisplayed()
    }
}
