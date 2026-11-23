package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.text.input.InputTransformation
import androidx.compose.foundation.text.input.OutputTransformation
import androidx.compose.foundation.text.input.TextFieldDecorator
import androidx.compose.foundation.text.input.TextFieldLineLimits
import androidx.compose.foundation.text.input.rememberTextFieldState
import androidx.compose.foundation.text.input.setTextAndPlaceCursorAtEnd
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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.error
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.password
import androidx.compose.ui.semantics.semantics
import androidx.compose.material3.ColorScheme
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
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

internal fun fieldHelperColor(isError: Boolean, scheme: ColorScheme): Color =
    if (isError) scheme.error else scheme.onSurfaceVariant

private fun Modifier.fieldSemantics(
    isError: Boolean,
    helper: String,
    visualTransformation: VisualTransformation,
): Modifier = semantics {
    if (isError) error(helper)
    if (visualTransformation is PasswordVisualTransformation) password()
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
    placeholder: String = "",
    inputTransformation: InputTransformation? = null,
    outputTransformation: OutputTransformation? = null,
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
            placeholder = placeholder,
            inputTransformation = inputTransformation,
            outputTransformation = outputTransformation,
        )
        return
    }
    val isError = state == SolventaFieldState.Error
    val fieldModifier = modifier
        .fillMaxWidth()
        .testTag(testTag ?: "solventa_text_field")
        .fieldSemantics(isError = isError, helper = helper, visualTransformation = visualTransformation)
    val readOnly = state == SolventaFieldState.ReadOnly
    val labelContent: @Composable () -> Unit = { Text(label) }
    val helperContent: @Composable (() -> Unit)? = if (helper.isEmpty()) {
        null
    } else {
        {
            Text(
                helper,
                modifier = Modifier.semantics {
                    if (isError) liveRegion = LiveRegionMode.Polite
                },
            )
        }
    }
    val placeholderContent: @Composable (() -> Unit)? = if (placeholder.isEmpty()) {
        null
    } else {
        { Text(placeholder) }
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
            placeholder = placeholderContent,
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
            placeholder = placeholderContent,
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
    placeholder: String,
    inputTransformation: InputTransformation?,
    outputTransformation: OutputTransformation?,
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
                .heightIn(min = SolventaSpacing.minTouch)
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
                val fieldModifier = Modifier
                    .weight(1f)
                    .testTag(testTag ?: "solventa_text_field")
                    .fieldSemantics(isError = isError, helper = helper, visualTransformation = visualTransformation)
                val fieldStyle = SolventaTypography.amount.copy(
                    color = MaterialTheme.colorScheme.onSurface,
                )
                if (inputTransformation != null) {
                    BoundedTextField(
                        value = value,
                        onValueChange = onValueChange,
                        modifier = fieldModifier,
                        readOnly = readOnly,
                        textStyle = fieldStyle,
                        keyboardOptions = keyboardOptions,
                        placeholder = placeholder,
                        inputTransformation = inputTransformation,
                        outputTransformation = outputTransformation,
                    )
                } else {
                    BasicTextField(
                        value = value,
                        onValueChange = onValueChange,
                        modifier = fieldModifier,
                        readOnly = readOnly,
                        textStyle = fieldStyle,
                        keyboardOptions = keyboardOptions,
                        visualTransformation = visualTransformation,
                        singleLine = true,
                        cursorBrush = SolidColor(MaterialTheme.colorScheme.primary),
                        decorationBox = { innerTextField ->
                            PlaceholderBox(value = value, placeholder = placeholder, innerTextField = innerTextField)
                        },
                    )
                }
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
                color = fieldHelperColor(isError, MaterialTheme.colorScheme),
                modifier = Modifier.semantics {
                    if (isError) liveRegion = LiveRegionMode.Polite
                },
            )
        }
    }
}

@Composable
private fun BoundedTextField(
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier,
    readOnly: Boolean,
    textStyle: TextStyle,
    keyboardOptions: KeyboardOptions,
    placeholder: String,
    inputTransformation: InputTransformation,
    outputTransformation: OutputTransformation?,
) {
    val textState = rememberTextFieldState(value)
    var lastEmitted by remember { mutableStateOf(value) }
    LaunchedEffect(textState) {
        snapshotFlow { textState.text.toString() }.collect { next ->
            if (next != lastEmitted) {
                lastEmitted = next
                onValueChange(next)
            }
        }
    }
    SideEffect {
        if (value != lastEmitted && value != textState.text.toString()) {
            lastEmitted = value
            textState.setTextAndPlaceCursorAtEnd(value)
        }
    }
    val shown = textState.text.toString()
    BasicTextField(
        state = textState,
        modifier = modifier,
        readOnly = readOnly,
        inputTransformation = inputTransformation,
        outputTransformation = outputTransformation,
        textStyle = textStyle,
        keyboardOptions = keyboardOptions,
        lineLimits = TextFieldLineLimits.SingleLine,
        cursorBrush = SolidColor(MaterialTheme.colorScheme.primary),
        decorator = TextFieldDecorator { innerTextField ->
            PlaceholderBox(value = shown, placeholder = placeholder, innerTextField = innerTextField)
        },
    )
}

@Composable
private fun PlaceholderBox(
    value: String,
    placeholder: String,
    innerTextField: @Composable () -> Unit,
) {
    Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.CenterStart) {
        if (value.isEmpty() && placeholder.isNotEmpty()) {
            Text(
                text = placeholder,
                style = SolventaTypography.amount.copy(
                    color = fieldHelperColor(isError = false, MaterialTheme.colorScheme),
                ),
                maxLines = 1,
            )
        }
        innerTextField()
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
