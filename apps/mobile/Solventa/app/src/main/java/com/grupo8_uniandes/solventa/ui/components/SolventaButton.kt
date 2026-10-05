package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

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
) {
    val buttonModifier = modifier
        .height(SolventaSpacing.buttonHeight)
        .testTag(testTag ?: "solventa_button_${style.name.lowercase()}")
    val shape = SolventaSpacing.buttonRadius
    when (style) {
        SolventaButtonStyle.Filled -> Button(onClick, buttonModifier, enabled, shape = shape) { Text(text) }
        SolventaButtonStyle.Tonal -> FilledTonalButton(onClick, buttonModifier, enabled, shape = shape) { Text(text) }
        SolventaButtonStyle.Outlined -> OutlinedButton(onClick, buttonModifier, enabled, shape = shape) { Text(text) }
        SolventaButtonStyle.Text -> TextButton(onClick, buttonModifier, enabled, shape = shape) { Text(text) }
    }
}
