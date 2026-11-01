package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsPropertyKey
import androidx.compose.ui.semantics.semantics
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

val SolventaButtonStyleKey = SemanticsPropertyKey<SolventaButtonStyle>("SolventaButtonStyle")

enum class SolventaButtonStyle {
    Filled,
    Tonal,
    Outlined,
    Text,
}

@Composable
fun SolventaButton(
    text: String,
    style: SolventaButtonStyle,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    testTag: String? = null,
    contentPadding: PaddingValues? = null,
) {
    val buttonModifier = modifier
        .height(SolventaSpacing.buttonHeight)
        .semantics { set(SolventaButtonStyleKey, style) }
        .testTag(testTag ?: "solventa_button_${style.name.lowercase()}")
    val shape = SolventaSpacing.buttonRadius
    val padding = contentPadding ?: ButtonDefaults.ContentPadding
    when (style) {
        SolventaButtonStyle.Filled -> Button(
            onClick = onClick,
            modifier = buttonModifier,
            enabled = enabled,
            shape = shape,
            contentPadding = padding,
        ) { Text(text) }
        SolventaButtonStyle.Tonal -> FilledTonalButton(
            onClick = onClick,
            modifier = buttonModifier,
            enabled = enabled,
            shape = shape,
            contentPadding = padding,
        ) { Text(text) }
        SolventaButtonStyle.Outlined -> OutlinedButton(
            onClick = onClick,
            modifier = buttonModifier,
            enabled = enabled,
            shape = shape,
            contentPadding = padding,
        ) { Text(text) }
        SolventaButtonStyle.Text -> TextButton(
            onClick = onClick,
            modifier = buttonModifier,
            enabled = enabled,
            shape = shape,
            contentPadding = padding,
        ) { Text(text) }
    }
}
