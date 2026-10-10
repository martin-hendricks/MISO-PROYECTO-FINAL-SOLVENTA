package com.grupo8_uniandes.solventa.registration

import android.Manifest
import android.app.Application
import android.content.Context
import android.net.Uri
import androidx.activity.ComponentActivity
import androidx.activity.compose.LocalActivityResultRegistryOwner
import androidx.activity.result.ActivityResultRegistry
import androidx.activity.result.ActivityResultRegistryOwner
import androidx.activity.result.contract.ActivityResultContract
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.core.app.ActivityOptionsCompat
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.ui.registration.LoginPlaceholder
import com.grupo8_uniandes.solventa.ui.registration.OnboardingPhotoInjector
import com.grupo8_uniandes.solventa.ui.registration.OnboardingScreen
import com.grupo8_uniandes.solventa.ui.registration.OnboardingUiState
import com.grupo8_uniandes.solventa.ui.registration.captureUri
import com.grupo8_uniandes.solventa.ui.registration.prepareCaptureFile
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows
import org.robolectric.annotation.Config
import java.io.File

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class OnboardingScreenTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @After
    fun clearInjector() {
        OnboardingPhotoInjector.next = null
        OnboardingPhotoInjector.captureUri = null
    }

    @Test
    fun givenEmptyForm_whenShown_thenCopyAndDisabledContinuar() {
        show(OnboardingUiState())

        rule.onNodeWithText("Solventa").assertIsDisplayed()
        rule.onNodeWithText("1 de 2 · Cuenta").assertIsDisplayed()
        rule.onNodeWithText("Crea tu cuenta").assertIsDisplayed()
        rule.onNodeWithText("Datos, documento y contraseña para ingresar después.").assertIsDisplayed()
        rule.onNodeWithText("Como aparece en tu documento").assertIsDisplayed()
        rule.onNodeWithText("El mismo que usarás para ingresar").assertIsDisplayed()
        rule.onNodeWithTag("action_continuar").assertIsNotEnabled()
        rule.onNodeWithTag("action_ya_tengo_cuenta").performScrollTo().assertIsDisplayed()
    }

    @Test
    fun givenFields_whenEdited_thenCallbacksReceiveTheText() {
        var name by mutableStateOf("")
        var surnames by mutableStateOf("")
        var email by mutableStateOf("")
        var type by mutableStateOf("")
        var number by mutableStateOf("")
        var password by mutableStateOf("")
        rule.setContent {
            SolventaTheme {
                OnboardingScreen(
                    state = OnboardingUiState(
                        givenName = name,
                        surnames = surnames,
                        email = email,
                        documentType = type,
                        documentNumber = number,
                        password = password,
                    ),
                    onGivenName = { name = it },
                    onSurnames = { surnames = it },
                    onEmail = { email = it },
                    onDocumentType = { type = it },
                    onDocumentNumber = { number = it },
                    onPassword = { password = it },
                    onPhotoAttached = {},
                    onPhotoDeclined = {},
                    onContinue = {},
                    onExistingAccount = {},
                )
            }
        }

        rule.onNodeWithTag("field_nombre").performTextInput("Camila")
        rule.onNodeWithTag("field_apellidos").performTextInput("Restrepo")
        rule.onNodeWithTag("field_correo").performTextInput("camila@correo.com")
        rule.onNodeWithTag("field_tipo").performTextInput("CC")
        rule.onNodeWithTag("field_numero").performTextInput("1023456789")
        rule.onNodeWithTag("field_contrasena").performTextInput("secret")

        assertEquals("Camila", name)
        assertEquals("Restrepo", surnames)
        assertEquals("camila@correo.com", email)
        assertEquals("CC", type)
        assertEquals("1023456789", number)
        assertEquals("secret", password)
    }

    @Test
    fun givenInvalidEmailAndReadyForm_whenActionsPressed_thenErrorStaysAndHandoffsRun() {
        var continued = 0
        var existing = 0
        show(
            state = readyState(email = "camila", emailError = true),
            onContinue = { continued += 1 },
            onExistingAccount = { existing += 1 },
        )

        rule.onNodeWithText("El correo no es válido.").performScrollTo().assertIsDisplayed()
        rule.onNodeWithTag("action_continuar").performScrollTo().assertIsEnabled()
        rule.onNodeWithTag("action_continuar").performClick()
        rule.onNodeWithTag("action_ya_tengo_cuenta").performScrollTo().performClick()
        assertEquals(1, continued)
        assertEquals(1, existing)
    }

    @Test
    fun givenInjectedPhoto_whenFotoPressed_thenBytesAttachOrDecline() {
        var attached: ByteArray? = null
        var declined = 0
        show(
            state = OnboardingUiState(),
            onPhotoAttached = { attached = it },
            onPhotoDeclined = { declined += 1 },
        )

        OnboardingPhotoInjector.next = byteArrayOf(4, 5)
        rule.onNodeWithTag("action_foto").performScrollTo().performClick()
        assertTrue(byteArrayOf(4, 5).contentEquals(attached))

        OnboardingPhotoInjector.next = byteArrayOf()
        rule.onNodeWithTag("action_foto").performClick()
        assertEquals(1, declined)
    }

    @Test
    fun givenCameraDenied_whenFotoPressed_thenPhotoIsDeclined() {
        var declined = 0
        show(
            state = OnboardingUiState(),
            onPhotoDeclined = { declined += 1 },
            registry = ImmediateRegistry(permissionGranted = false, pictureResults = ArrayDeque()),
        )

        rule.onNodeWithTag("action_foto").performScrollTo().performClick()
        assertEquals(1, declined)
    }

    @Test
    fun givenCameraGranted_whenPictureReturns_thenBytesAttachOrDecline() {
        var attached: ByteArray? = null
        var declined = 0
        OnboardingPhotoInjector.captureUri = Uri.parse("content://solventa/capture")
        show(
            state = OnboardingUiState(),
            onPhotoAttached = { attached = it },
            onPhotoDeclined = { declined += 1 },
            registry = ImmediateRegistry(
                permissionGranted = true,
                pictureResults = ArrayDeque(listOf(true, true, false, true)),
            ),
        )
        seedCapture(byteArrayOf(9, 8, 7))

        rule.onNodeWithTag("action_foto").performScrollTo().performClick()
        assertTrue(byteArrayOf(9, 8, 7).contentEquals(attached))

        seedCapture(byteArrayOf())
        rule.onNodeWithTag("action_foto").performClick()
        rule.onNodeWithTag("action_foto").performClick()
        val missing = File(rule.activity.cacheDir, "registration/capture.jpg")
        missing.delete()
        missing.mkdir()
        rule.onNodeWithTag("action_foto").performClick()
        assertEquals(3, declined)
    }

    @Test
    fun givenPermissionAlreadyHeld_whenFotoPressed_thenCaptureLaunches() {
        var attached: ByteArray? = null
        Shadows.shadowOf(ApplicationProvider.getApplicationContext<Application>())
            .grantPermissions(Manifest.permission.CAMERA)
        OnboardingPhotoInjector.captureUri = Uri.parse("content://solventa/capture")
        show(
            state = OnboardingUiState(),
            onPhotoAttached = { attached = it },
            registry = ImmediateRegistry(
                permissionGranted = false,
                pictureResults = ArrayDeque(listOf(true)),
            ),
        )
        seedCapture(byteArrayOf(1))

        rule.onNodeWithTag("action_foto").performScrollTo().performClick()
        assertTrue(byteArrayOf(1).contentEquals(attached))
    }

    @Test
    fun givenPermissionAlreadyHeld_whenNoUriOverride_thenCaptureFileIsPrepared() {
        Shadows.shadowOf(ApplicationProvider.getApplicationContext<Application>())
            .grantPermissions(Manifest.permission.CAMERA)
        show(
            state = OnboardingUiState(),
            registry = ImmediateRegistry(permissionGranted = false, pictureResults = ArrayDeque(listOf(true))),
        )

        try {
            rule.onNodeWithTag("action_foto").performScrollTo().performClick()
        } catch (error: IllegalArgumentException) {
            assertTrue(error.message.orEmpty().contains("configured root"))
        }
        assertTrue(File(rule.activity.cacheDir, "registration/capture.jpg").isFile)
    }

    @Test
    fun givenCaptureFile_whenUriIsBuilt_thenFileExists() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val file = File(context.cacheDir, "registration/capture.jpg")
        file.delete()
        try {
            val uri = captureUri(context, file)
            assertEquals("content", uri.scheme)
        } catch (error: IllegalArgumentException) {
            assertTrue(error.message.orEmpty().contains("configured root"))
        }
        assertTrue(file.isFile)

        val existing = File(context.cacheDir, "registration/again.jpg")
        existing.parentFile?.mkdirs()
        existing.writeBytes(byteArrayOf(1))
        prepareCaptureFile(existing)
        assertTrue(existing.isFile)

        val loose = File("capture-coverage.jpg")
        try {
            prepareCaptureFile(loose)
            assertTrue(loose.isFile)
            prepareCaptureFile(loose)
        } finally {
            loose.delete()
        }
    }

    @Test
    fun givenModifier_whenLoginPlaceholderShown_thenLoginCopyStays() {
        rule.setContent {
            SolventaTheme {
                Column {
                    LoginPlaceholder(modifier = Modifier)
                    LoginPlaceholder()
                }
            }
        }

        rule.onAllNodesWithText("Login").assertCountEquals(2)
    }

    private fun seedCapture(bytes: ByteArray) {
        val file = File(rule.activity.cacheDir, "registration/capture.jpg")
        file.parentFile?.mkdirs()
        file.writeBytes(bytes)
    }

    private fun show(
        state: OnboardingUiState,
        onGivenName: (String) -> Unit = {},
        onSurnames: (String) -> Unit = {},
        onEmail: (String) -> Unit = {},
        onDocumentType: (String) -> Unit = {},
        onDocumentNumber: (String) -> Unit = {},
        onPassword: (String) -> Unit = {},
        onPhotoAttached: (ByteArray) -> Unit = {},
        onPhotoDeclined: () -> Unit = {},
        onContinue: () -> Unit = {},
        onExistingAccount: () -> Unit = {},
        registry: ActivityResultRegistry? = null,
    ) {
        rule.setContent {
            SolventaTheme {
                RegistryHost(registry) {
                    OnboardingScreen(
                        state = state,
                        onGivenName = onGivenName,
                        onSurnames = onSurnames,
                        onEmail = onEmail,
                        onDocumentType = onDocumentType,
                        onDocumentNumber = onDocumentNumber,
                        onPassword = onPassword,
                        onPhotoAttached = onPhotoAttached,
                        onPhotoDeclined = onPhotoDeclined,
                        onContinue = onContinue,
                        onExistingAccount = onExistingAccount,
                        modifier = Modifier,
                    )
                }
            }
        }
    }

    private fun readyState(email: String, emailError: Boolean) = OnboardingUiState(
        givenName = "Camila",
        surnames = "Restrepo",
        email = email,
        documentType = "CC",
        documentNumber = "1023456789",
        password = "secret",
        hasPhoto = true,
        emailError = emailError,
        continuarEnabled = true,
    )
}

@Composable
private fun RegistryHost(
    registry: ActivityResultRegistry?,
    content: @Composable () -> Unit,
) {
    if (registry == null) {
        content()
    } else {
        androidx.compose.runtime.CompositionLocalProvider(
            LocalActivityResultRegistryOwner provides object : ActivityResultRegistryOwner {
                override val activityResultRegistry: ActivityResultRegistry = registry
            },
            content = content,
        )
    }
}

private class ImmediateRegistry(
    private val permissionGranted: Boolean,
    private val pictureResults: ArrayDeque<Boolean>,
    private val beforePicture: () -> Unit = {},
) : ActivityResultRegistry() {
    override fun <I, O> onLaunch(
        requestCode: Int,
        contract: ActivityResultContract<I, O>,
        input: I,
        options: ActivityOptionsCompat?,
    ) {
        val result = when (contract) {
            is ActivityResultContracts.RequestPermission -> permissionGranted
            is ActivityResultContracts.TakePicture -> {
                beforePicture()
                pictureResults.removeFirst()
            }
            else -> error("unexpected contract")
        }
        @Suppress("UNCHECKED_CAST")
        dispatchResult(requestCode, result as O)
    }
}
