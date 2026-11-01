package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.theme.HankenGrotesk
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

enum class SolventaFieldStyle {
    Outlined,
    Filled,
}

enum class SolventaFieldState {
    Default,
    Error,
    ReadOnly,
}

@Composable
fun SolventaTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    helper: String,
    modifier: Modifier = Modifier,
    style: SolventaFieldStyle = SolventaFieldStyle.Outlined,
    state: SolventaFieldState = SolventaFieldState.Default,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    visualTransformation: VisualTransformation = VisualTransformation.None,
    trailingIcon: @Composable (() -> Unit)? = null,
    testTag: String? = null,
    externalLabel: Boolean = false,
) {
    if (externalLabel) {
        ExternalLabelField(
            value = value,
            onValueChange = onValueChange,
            label = label,
            helper = helper,
            state = state,
            keyboardOptions = keyboardOptions,
            visualTransformation = visualTransformation,
            modifier = modifier,
            trailingIcon = trailingIcon,
            testTag = testTag,
        )
        return
    }
    val fieldModifier = modifier.fillMaxWidth().testTag(testTag ?: "solventa_text_field")
    val isError = state == SolventaFieldState.Error
    val readOnly = state == SolventaFieldState.ReadOnly
    val labelContent: @Composable () -> Unit = { Text(label) }
    val helperContent: @Composable (() -> Unit)? = if (helper.isEmpty()) {
        null
    } else {
        { Text(helper) }
    }
    when (style) {
        SolventaFieldStyle.Outlined -> OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            modifier = fieldModifier,
            readOnly = readOnly,
            label = labelContent,
            supportingText = helperContent,
            isError = isError,
            keyboardOptions = keyboardOptions,
            visualTransformation = visualTransformation,
            trailingIcon = trailingIcon,
        )
        SolventaFieldStyle.Filled -> TextField(
            value = value,
            onValueChange = onValueChange,
            modifier = fieldModifier,
            readOnly = readOnly,
            label = labelContent,
            supportingText = helperContent,
            isError = isError,
            keyboardOptions = keyboardOptions,
            visualTransformation = visualTransformation,
            trailingIcon = trailingIcon,
        )
    }
}

@Composable
private fun ExternalLabelField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    helper: String,
    state: SolventaFieldState,
    keyboardOptions: KeyboardOptions,
    visualTransformation: VisualTransformation,
    trailingIcon: @Composable (() -> Unit)?,
    modifier: Modifier,
    testTag: String?,
) {
    val isError = state == SolventaFieldState.Error
    val readOnly = state == SolventaFieldState.ReadOnly
    val shape = RoundedCornerShape(8.dp)
    val borderColor = if (isError) {
        MaterialTheme.colorScheme.error
    } else {
        MaterialTheme.colorScheme.outlineVariant
    }
    Column(modifier.fillMaxWidth()) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(SolventaSpacing.s4))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(SolventaSpacing.minTouch)
                .clip(shape)
                .background(MaterialTheme.colorScheme.surfaceContainerLowest)
                .border(1.dp, borderColor, shape)
                .padding(horizontal = SolventaSpacing.s12),
            contentAlignment = Alignment.CenterStart,
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                BasicTextField(
                    value = value,
                    onValueChange = onValueChange,
                    modifier = Modifier
                        .weight(1f)
                        .testTag(testTag ?: "solventa_text_field"),
                    readOnly = readOnly,
                    textStyle = SolventaTypography.amount.copy(
                        color = MaterialTheme.colorScheme.onSurface,
                    ),
                    keyboardOptions = keyboardOptions,
                    visualTransformation = visualTransformation,
                    singleLine = true,
                    cursorBrush = SolidColor(MaterialTheme.colorScheme.primary),
                )
                trailingIcon?.invoke()
            }
        }
        if (helper.isNotEmpty()) {
            Spacer(Modifier.height(SolventaSpacing.s4))
            Text(
                text = helper,
                style = TextStyle(
                    fontFamily = HankenGrotesk,
                    fontWeight = FontWeight.Normal,
                    fontSize = 12.sp,
                    lineHeight = 16.sp,
                ),
                color = if (isError) {
                    MaterialTheme.colorScheme.error
                } else {
                    MaterialTheme.colorScheme.outline
                },
            )
        }
    }
}

@Composable
fun SolventaPasswordToggle(
    visible: Boolean,
    onToggle: () -> Unit,
    testTag: String,
) {
    IconButton(
        onClick = onToggle,
        modifier = Modifier.testTag(testTag),
    ) {
        Icon(
            imageVector = if (visible) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
            contentDescription = stringResource(
                if (visible) R.string.password_hide else R.string.password_show,
            ),
        )
    }
}
