package com.grupo8_uniandes.solventa.ui.registration

import android.graphics.BitmapFactory
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathOperation
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaSelect
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun LivenessScreen(
    state: LivenessUiState,
    onGivenName: (String) -> Unit,
    onSurnames: (String) -> Unit,
    onEmail: (String) -> Unit,
    onDocumentType: (String) -> Unit,
    onDocumentNumber: (String) -> Unit,
    onPassword: (String) -> Unit,
    onContinue: () -> Unit,
    onExistingAccount: () -> Unit,
    onShutter: () -> Unit = {},
    onRepeat: () -> Unit = {},
    onRetry: () -> Unit = {},
    onContinueCamera: () -> Unit = {},
    onContinueWithDocument: () -> Unit = {},
    preview: @Composable () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    if (state.phase != LivenessPhase.Form) {
        LivenessCameraContent(
            state = state,
            onShutter = onShutter,
            onRepeat = onRepeat,
            onRetry = onRetry,
            onContinue = onContinueCamera,
            onContinueWithDocument = onContinueWithDocument,
            onExistingAccount = onExistingAccount,
            preview = preview,
            modifier = modifier,
        )
        return
    }
    var typeExpanded by remember { mutableStateOf(false) }
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface)
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_prueba_de_vida"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.onboarding_wordmark),
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Text(
            text = stringResource(R.string.liveness_step),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = stringResource(R.string.liveness_title),
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = stringResource(R.string.liveness_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        SolventaTextField(
            value = state.givenName,
            onValueChange = onGivenName,
            label = stringResource(R.string.onboarding_nombre),
            helper = stringResource(R.string.onboarding_nombre_hint),
            testTag = "field_liveness_nombre",
        )
        SolventaTextField(
            value = state.surnames,
            onValueChange = onSurnames,
            label = stringResource(R.string.onboarding_apellidos),
            helper = "",
            testTag = "field_liveness_apellidos",
        )
        SolventaTextField(
            value = state.email,
            onValueChange = onEmail,
            label = stringResource(R.string.onboarding_correo),
            helper = stringResource(R.string.onboarding_correo_hint),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            testTag = "field_liveness_correo",
        )
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s4),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            SolventaSelect(
                label = stringResource(R.string.onboarding_tipo),
                value = state.documentType,
                options = state.documentTypeOptions,
                expanded = typeExpanded,
                onExpandedChange = { typeExpanded = it },
                onSelect = onDocumentType,
            )
            SolventaTextField(
                value = state.documentNumber,
                onValueChange = onDocumentNumber,
                label = stringResource(R.string.onboarding_numero),
                helper = "",
                modifier = Modifier.weight(1f),
                testTag = "field_liveness_numero",
            )
        }
        SolventaTextField(
            value = state.password,
            onValueChange = onPassword,
            label = stringResource(R.string.onboarding_contrasena),
            helper = "",
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            testTag = "field_liveness_contrasena",
        )
        SolventaButton(
            text = stringResource(R.string.action_continuar_onboarding),
            style = SolventaButtonStyle.Filled,
            onClick = onContinue,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_liveness_continuar",
        )
        SolventaButton(
            text = stringResource(R.string.action_ya_tengo_cuenta),
            style = SolventaButtonStyle.Text,
            onClick = onExistingAccount,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_liveness_ya_tengo_cuenta",
        )
    }
}

@Composable
internal fun LivenessCameraContent(
    state: LivenessUiState,
    onShutter: () -> Unit,
    onRepeat: () -> Unit,
    onRetry: () -> Unit,
    onContinue: () -> Unit,
    onContinueWithDocument: () -> Unit,
    onExistingAccount: () -> Unit,
    preview: @Composable () -> Unit,
    modifier: Modifier = Modifier,
) {
    val hint = stringResource(R.string.liveness_camera_hint)
    val shutterName = stringResource(R.string.liveness_shutter)
    val photoName = stringResource(R.string.liveness_photo_taken)
    val status = when (state.phase) {
        LivenessPhase.Sending -> stringResource(R.string.liveness_sending)
        LivenessPhase.Failed -> stringResource(R.string.liveness_failed)
        LivenessPhase.Denied -> stringResource(R.string.liveness_denied)
        LivenessPhase.Unavailable -> stringResource(R.string.liveness_unavailable)
        else -> null
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s8)
            .testTag("screen_prueba_de_vida"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.liveness_step),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.testTag("liveness_camera_step"),
        )
        Text(
            text = stringResource(R.string.liveness_title),
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.semantics { heading() }.testTag("liveness_camera_title"),
        )
        Text(
            text = stringResource(R.string.liveness_camera_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.testTag("liveness_camera_body"),
        )
        if (status != null) {
            Text(
                text = status,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier
                    .semantics { liveRegion = LiveRegionMode.Polite }
                    .testTag("liveness_status"),
            )
        }
        if (state.phase != LivenessPhase.Denied) {
            CameraFrame(
                hint = hint,
                photo = state.photo,
                showPhoto = state.phase == LivenessPhase.Passed ||
                    state.phase == LivenessPhase.Sending ||
                    state.phase == LivenessPhase.Unavailable,
                photoName = photoName,
                preview = preview,
            )
        }
        if (state.phase == LivenessPhase.Camera || state.phase == LivenessPhase.Sending) {
            Shutter(
                name = shutterName,
                enabled = state.phase != LivenessPhase.Sending,
                onClick = onShutter,
                modifier = Modifier.align(Alignment.CenterHorizontally),
            )
        }
        if (state.phase == LivenessPhase.Passed) {
            SolventaButton(
                text = stringResource(R.string.action_continuar_onboarding),
                style = SolventaButtonStyle.Filled,
                onClick = onContinue,
                modifier = Modifier.fillMaxWidth().heightIn(min = SolventaSpacing.minTouch),
                testTag = "action_liveness_continuar_camara",
            )
        }
        if (state.phase == LivenessPhase.Failed || state.phase == LivenessPhase.Denied) {
            SolventaButton(
                text = stringResource(R.string.action_repetir_foto),
                style = SolventaButtonStyle.Filled,
                onClick = onRepeat,
                modifier = Modifier.fillMaxWidth().heightIn(min = SolventaSpacing.minTouch),
                testTag = "action_liveness_repetir",
            )
        }
        if (state.phase == LivenessPhase.Unavailable) {
            SolventaButton(
                text = stringResource(R.string.action_reintentar),
                style = SolventaButtonStyle.Filled,
                onClick = onRetry,
                modifier = Modifier.fillMaxWidth().heightIn(min = SolventaSpacing.minTouch),
                testTag = "action_liveness_reintentar",
            )
        }
        if (state.phase == LivenessPhase.Failed ||
            state.phase == LivenessPhase.Denied ||
            state.phase == LivenessPhase.Unavailable
        ) {
            SolventaButton(
                text = stringResource(R.string.action_continuar_documento),
                style = SolventaButtonStyle.Text,
                onClick = onContinueWithDocument,
                modifier = Modifier.fillMaxWidth().heightIn(min = SolventaSpacing.minTouch),
                testTag = "action_liveness_documento",
            )
        }
        SolventaButton(
            text = stringResource(R.string.action_ya_tengo_cuenta),
            style = SolventaButtonStyle.Text,
            onClick = onExistingAccount,
            modifier = Modifier.fillMaxWidth().heightIn(min = SolventaSpacing.minTouch),
            testTag = "action_liveness_ya_tengo_cuenta",
        )
    }
}

@Composable
private fun CameraFrame(
    hint: String,
    photo: ByteArray?,
    showPhoto: Boolean,
    photoName: String,
    preview: @Composable () -> Unit,
) {
    val veil = MaterialTheme.colorScheme.inverseSurface.copy(alpha = 0.55f)
    val stroke = MaterialTheme.colorScheme.primary
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(480.dp)
            .clip(RoundedCornerShape(24.dp))
            .background(MaterialTheme.colorScheme.inverseSurface)
            .semantics { contentDescription = hint }
            .testTag("liveness_camera_preview"),
    ) {
        if (showPhoto && photo != null) {
            val bitmap = remember(photo) {
                BitmapFactory.decodeByteArray(photo, 0, photo.size)?.asImageBitmap()
            }
            if (bitmap != null) {
                Image(
                    bitmap = bitmap,
                    contentDescription = photoName,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize().testTag("liveness_photo"),
                )
            }
        } else {
            preview()
        }
        Canvas(Modifier.fillMaxSize()) {
            val ovalWidth = 236.dp.toPx()
            val ovalHeight = 312.dp.toPx()
            val oval = Rect(
                offset = Offset((size.width - ovalWidth) / 2f, 56.dp.toPx()),
                size = Size(ovalWidth, ovalHeight),
            )
            val cut = Path().apply { addOval(oval) }
            val full = Path().apply { addRect(Rect(Offset.Zero, size)) }
            val dim = Path()
            dim.op(full, cut, PathOperation.Difference)
            drawPath(dim, veil)
            drawOval(color = stroke, topLeft = oval.topLeft, size = oval.size, style = Stroke(width = 3.dp.toPx()))
        }
        Text(
            text = hint,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.inverseOnSurface,
            textAlign = TextAlign.Center,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = SolventaSpacing.s16)
                .fillMaxWidth()
                .clearAndSetSemantics { },
        )
    }
}

@Composable
private fun Shutter(name: String, enabled: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .size(72.dp)
            .clip(CircleShape)
            .background(MaterialTheme.colorScheme.primary)
            .semantics {
                role = Role.Button
                contentDescription = name
            }
            .clickable(enabled = enabled, onClick = onClick)
            .testTag("action_liveness_shutter"),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = Icons.Filled.PhotoCamera,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onPrimary,
            modifier = Modifier.size(28.dp),
        )
    }
}
