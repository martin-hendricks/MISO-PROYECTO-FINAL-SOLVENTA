package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag

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
) {
    val fieldModifier = modifier.fillMaxWidth().testTag("solventa_text_field")
    val isError = state == SolventaFieldState.Error
    val readOnly = state == SolventaFieldState.ReadOnly
    val labelContent: @Composable () -> Unit = { Text(label) }
    val helperContent: @Composable () -> Unit = { Text(helper) }
    when (style) {
        SolventaFieldStyle.Outlined -> OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            modifier = fieldModifier,
            readOnly = readOnly,
            label = labelContent,
            supportingText = helperContent,
            isError = isError,
        )
        SolventaFieldStyle.Filled -> TextField(
            value = value,
            onValueChange = onValueChange,
            modifier = fieldModifier,
            readOnly = readOnly,
            label = labelContent,
            supportingText = helperContent,
            isError = isError,
        )
    }
}
