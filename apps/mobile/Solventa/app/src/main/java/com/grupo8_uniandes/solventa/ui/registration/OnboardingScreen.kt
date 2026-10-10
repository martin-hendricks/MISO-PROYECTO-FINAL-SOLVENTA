package com.grupo8_uniandes.solventa.ui.registration

import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import java.io.File

/**
 * Instrumented tests set [next] so the photo action can attach or decline
 * without a camera app. Unit tests set [captureUri] so the camera launch
 * does not ask FileProvider for a content uri. Production leaves both null.
 */
internal object OnboardingPhotoInjector {
    var next: ByteArray? = null

    /** Unit tests supply a uri so the camera launch does not depend on FileProvider. */
    var captureUri: Uri? = null

    fun consume(): ByteArray? = next.also { next = null }
}

@Composable
fun OnboardingScreen(
    state: OnboardingUiState,
    onGivenName: (String) -> Unit,
    onSurnames: (String) -> Unit,
    onEmail: (String) -> Unit,
    onDocumentType: (String) -> Unit,
    onDocumentNumber: (String) -> Unit,
    onPassword: (String) -> Unit,
    onPhotoAttached: (ByteArray) -> Unit,
    onPhotoDeclined: () -> Unit,
    onContinue: () -> Unit,
    onExistingAccount: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val captureFile = remember {
        File(context.cacheDir, "registration/capture.jpg")
    }
    val takePicture = rememberLauncherForActivityResult(
        ActivityResultContracts.TakePicture(),
    ) { success ->
        val bytes = captureFile.takeIf { success && it.isFile }?.readBytes()
        if (bytes != null && bytes.isNotEmpty()) {
            onPhotoAttached(bytes)
        } else {
            onPhotoDeclined()
        }
    }
    val requestCamera = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (granted) {
            launchCapture(context, captureFile, takePicture::launch)
        } else {
            onPhotoDeclined()
        }
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface)
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_onboarding"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.onboarding_wordmark),
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Text(
            text = stringResource(R.string.onboarding_step),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = stringResource(R.string.onboarding_title),
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Text(
            text = stringResource(R.string.onboarding_intro),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = stringResource(R.string.onboarding_photo),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        SolventaTextField(
            value = state.givenName,
            onValueChange = onGivenName,
            label = stringResource(R.string.onboarding_nombre),
            helper = stringResource(R.string.onboarding_nombre_hint),
            testTag = "field_nombre",
        )
        SolventaTextField(
            value = state.surnames,
            onValueChange = onSurnames,
            label = stringResource(R.string.onboarding_apellidos),
            helper = "",
            testTag = "field_apellidos",
        )
        SolventaTextField(
            value = state.email,
            onValueChange = onEmail,
            label = stringResource(R.string.onboarding_correo),
            helper = stringResource(
                if (state.emailError) R.string.onboarding_correo_error else R.string.onboarding_correo_hint,
            ),
            state = if (state.emailError) SolventaFieldState.Error else SolventaFieldState.Default,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            testTag = "field_correo",
        )
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
        ) {
            SolventaTextField(
                value = state.documentType,
                onValueChange = onDocumentType,
                label = stringResource(R.string.onboarding_tipo),
                helper = "",
                modifier = Modifier.weight(1f),
                testTag = "field_tipo",
            )
            SolventaTextField(
                value = state.documentNumber,
                onValueChange = onDocumentNumber,
                label = stringResource(R.string.onboarding_numero),
                helper = "",
                modifier = Modifier.weight(1f),
                testTag = "field_numero",
            )
        }
        SolventaTextField(
            value = state.password,
            onValueChange = onPassword,
            label = stringResource(R.string.onboarding_contrasena),
            helper = "",
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            visualTransformation = PasswordVisualTransformation(),
            testTag = "field_contrasena",
        )
        SolventaButton(
            text = stringResource(R.string.onboarding_photo),
            style = SolventaButtonStyle.Outlined,
            onClick = {
                val injected = OnboardingPhotoInjector.consume()
                when {
                    injected == null -> {
                        val granted = ContextCompat.checkSelfPermission(
                            context,
                            Manifest.permission.CAMERA,
                        ) == PackageManager.PERMISSION_GRANTED
                        if (granted) {
                            launchCapture(context, captureFile, takePicture::launch)
                        } else {
                            requestCamera.launch(Manifest.permission.CAMERA)
                        }
                    }
                    injected.isEmpty() -> onPhotoDeclined()
                    else -> onPhotoAttached(injected)
                }
            },
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_foto",
        )
        SolventaButton(
            text = stringResource(R.string.action_continuar_onboarding),
            style = SolventaButtonStyle.Filled,
            onClick = onContinue,
            modifier = Modifier.fillMaxWidth(),
            enabled = state.continuarEnabled,
            testTag = "action_continuar",
        )
        SolventaButton(
            text = stringResource(R.string.action_ya_tengo_cuenta),
            style = SolventaButtonStyle.Text,
            onClick = onExistingAccount,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_ya_tengo_cuenta",
        )
    }
}

@Composable
fun LoginPlaceholder(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface)
            .testTag("screen_login"),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = stringResource(R.string.login_placeholder),
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
    }
}

private fun launchCapture(
    context: android.content.Context,
    file: File,
    launch: (Uri) -> Unit,
) {
    val override = OnboardingPhotoInjector.captureUri
    if (override != null) {
        prepareCaptureFile(file)
        launch(override)
    } else {
        launch(captureUri(context, file))
    }
}

internal fun captureUri(context: android.content.Context, file: File): Uri {
    prepareCaptureFile(file)
    return FileProvider.getUriForFile(
        context,
        "${context.packageName}.fileprovider",
        file,
    )
}

internal fun prepareCaptureFile(file: File) {
    file.parentFile?.mkdirs()
    if (!file.exists()) file.createNewFile()
}
