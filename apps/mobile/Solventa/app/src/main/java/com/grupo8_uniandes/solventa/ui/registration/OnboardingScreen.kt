package com.grupo8_uniandes.solventa.ui.registration

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaBanner
import com.grupo8_uniandes.solventa.ui.components.SolventaBannerStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaPasswordToggle
import com.grupo8_uniandes.solventa.ui.components.SolventaSelect
import com.grupo8_uniandes.solventa.ui.components.SolventaSelectAppearance
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.components.SolventaTopBar
import com.grupo8_uniandes.solventa.ui.theme.HankenGrotesk
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import java.io.ByteArrayInputStream
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
    onPasswordConfirm: (String) -> Unit,
    onPhotoAttached: (ByteArray) -> Unit,
    onPhotoDeclined: () -> Unit,
    onContinue: () -> Unit,
    onExistingAccount: () -> Unit,
    showStep: Boolean = true,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    var typeExpanded by remember { mutableStateOf(false) }
    var passwordVisible by remember { mutableStateOf(false) }
    var confirmVisible by remember { mutableStateOf(false) }
    var previewBytes by remember { mutableStateOf<ByteArray?>(null) }
    LaunchedEffect(state.hasPhoto) {
        if (!state.hasPhoto) previewBytes = null
    }
    val captureFile = remember {
        File(context.cacheDir, "registration/capture.jpg")
    }
    val takePicture = rememberLauncherForActivityResult(
        ActivityResultContracts.TakePicture(),
    ) { success ->
        val bytes = captureFile.takeIf { success && it.isFile }?.readBytes()
        if (bytes != null && bytes.isNotEmpty()) {
            previewBytes = bytes
            onPhotoAttached(bytes)
        } else {
            previewBytes = null
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
    val outline = if (state.awaitingPhoto) {
        MaterialTheme.colorScheme.error
    } else {
        MaterialTheme.colorScheme.outlineVariant
    }
    val preview = remember(previewBytes) {
        previewBytes?.let { bytes -> decodeDocumentPhoto(bytes)?.asImageBitmap() }
    }
    val openCamera = {
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
            injected.isEmpty() -> {
                previewBytes = null
                onPhotoDeclined()
            }
            else -> {
                previewBytes = injected
                onPhotoAttached(injected)
            }
        }
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface)
            .testTag("screen_onboarding"),
    ) {
        SolventaTopBar(
            title = stringResource(R.string.onboarding_wordmark),
            showBack = false,
            onBack = {},
            titleStyle = TextStyle(
                fontFamily = HankenGrotesk,
                fontWeight = FontWeight.SemiBold,
                fontSize = 20.sp,
            ),
            minHeight = SolventaSpacing.s64,
        )
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
        ) {
            if (showStep) {
                Text(
                    text = stringResource(R.string.onboarding_step),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(
                text = stringResource(R.string.onboarding_title),
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Text(
                text = stringResource(R.string.onboarding_intro),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (state.unavailable) {
                SolventaBanner(
                    message = stringResource(R.string.login_unavailable_banner),
                    style = SolventaBannerStyle.Error,
                )
            }
            SolventaTextField(
                value = state.givenName,
                onValueChange = onGivenName,
                label = stringResource(R.string.onboarding_nombre),
                helper = stringResource(R.string.onboarding_nombre_hint),
                externalLabel = true,
                testTag = "field_nombre",
            )
            SolventaTextField(
                value = state.surnames,
                onValueChange = onSurnames,
                label = stringResource(R.string.onboarding_apellidos),
                helper = "",
                externalLabel = true,
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
                externalLabel = true,
                testTag = "field_correo",
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
                verticalAlignment = Alignment.Top,
            ) {
                SolventaSelect(
                    label = stringResource(R.string.onboarding_tipo),
                    value = state.documentType,
                    options = state.documentTypeOptions,
                    expanded = typeExpanded,
                    onExpandedChange = { typeExpanded = it },
                    onSelect = onDocumentType,
                    modifier = Modifier.weight(1f),
                    appearance = SolventaSelectAppearance.Field,
                )
                SolventaTextField(
                    value = state.documentNumber,
                    onValueChange = onDocumentNumber,
                    label = stringResource(R.string.onboarding_numero),
                    helper = "",
                    modifier = Modifier.weight(1f),
                    externalLabel = true,
                    testTag = "field_numero",
                )
            }
            val passwordsDiffer = state.password.isNotBlank() &&
                state.passwordConfirm.isNotBlank() &&
                state.password.trim() != state.passwordConfirm.trim()
            SolventaTextField(
                value = state.password,
                onValueChange = onPassword,
                label = stringResource(R.string.onboarding_contrasena),
                helper = stringResource(R.string.onboarding_contrasena_hint),
                keyboardOptions = KeyboardOptions(
                    keyboardType = if (passwordVisible) KeyboardType.Text else KeyboardType.Password,
                ),
                visualTransformation = if (passwordVisible) {
                    VisualTransformation.None
                } else {
                    PasswordVisualTransformation()
                },
                trailingIcon = {
                    SolventaPasswordToggle(
                        visible = passwordVisible,
                        onToggle = { passwordVisible = !passwordVisible },
                        testTag = "toggle_contrasena",
                    )
                },
                externalLabel = true,
                testTag = "field_contrasena",
            )
            SolventaTextField(
                value = state.passwordConfirm,
                onValueChange = onPasswordConfirm,
                label = stringResource(R.string.onboarding_confirmar),
                helper = stringResource(R.string.onboarding_confirmar_hint),
                state = if (passwordsDiffer) SolventaFieldState.Error else SolventaFieldState.Default,
                keyboardOptions = KeyboardOptions(
                    keyboardType = if (confirmVisible) KeyboardType.Text else KeyboardType.Password,
                ),
                visualTransformation = if (confirmVisible) {
                    VisualTransformation.None
                } else {
                    PasswordVisualTransformation()
                },
                trailingIcon = {
                    SolventaPasswordToggle(
                        visible = confirmVisible,
                        onToggle = { confirmVisible = !confirmVisible },
                        testTag = "toggle_confirmar",
                    )
                },
                externalLabel = true,
                testTag = "field_confirmar",
            )
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(120.dp)
                    .clip(SolventaSpacing.cardRadius)
                    .background(MaterialTheme.colorScheme.surfaceContainerLow)
                    .drawBehind {
                        drawRoundRect(
                            color = outline,
                            style = Stroke(
                                width = 1.dp.toPx(),
                                pathEffect = PathEffect.dashPathEffect(floatArrayOf(8.dp.toPx(), 8.dp.toPx())),
                            ),
                        )
                    }
                    .clickable(onClick = openCamera)
                    .testTag("action_foto"),
                contentAlignment = Alignment.Center,
            ) {
                if (state.hasPhoto && preview != null) {
                    Image(
                        bitmap = preview,
                        contentDescription = stringResource(R.string.onboarding_photo_preview),
                        modifier = Modifier
                            .fillMaxSize()
                            .testTag("preview_documento"),
                        contentScale = ContentScale.Crop,
                    )
                } else {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
                    ) {
                        Icon(
                            imageVector = Icons.Filled.PhotoCamera,
                            contentDescription = null,
                            modifier = Modifier.size(28.dp),
                            tint = MaterialTheme.colorScheme.primary,
                        )
                        Text(
                            text = stringResource(R.string.onboarding_photo_preview),
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.onSurface,
                        )
                        Text(
                            text = stringResource(R.string.onboarding_photo),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surfaceContainerLowest)
                .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Bottom))
                .padding(
                    start = SolventaSpacing.gutter,
                    end = SolventaSpacing.gutter,
                    top = SolventaSpacing.s8,
                    bottom = SolventaSpacing.gutter,
                ),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
        ) {
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

internal fun decodeDocumentPhoto(bytes: ByteArray): Bitmap? {
    val decoded = BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: return null
    val orientation = try {
        ExifInterface(ByteArrayInputStream(bytes)).getAttributeInt(
            ExifInterface.TAG_ORIENTATION,
            ExifInterface.ORIENTATION_NORMAL,
        )
    } catch (_: Throwable) {
        ExifInterface.ORIENTATION_NORMAL
    }
    val degrees = when (orientation) {
        ExifInterface.ORIENTATION_ROTATE_90 -> 90f
        ExifInterface.ORIENTATION_ROTATE_180 -> 180f
        ExifInterface.ORIENTATION_ROTATE_270 -> 270f
        else -> return decoded
    }
    val matrix = Matrix().apply { postRotate(degrees) }
    return Bitmap.createBitmap(decoded, 0, 0, decoded.width, decoded.height, matrix, true)
}
