package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun SolventaSelect(
    label: String,
    value: String,
    options: List<String>,
    expanded: Boolean,
    onExpandedChange: (Boolean) -> Unit,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier.testTag(if (expanded) "solventa_select_open" else "solventa_select_closed")) {
        SolventaButton(
            text = "$label: $value",
            style = SolventaButtonStyle.Outlined,
            onClick = { onExpandedChange(!expanded) },
        )
        if (expanded) {
            options.forEach { option ->
                Surface(
                    onClick = {
                        onSelect(option)
                        onExpandedChange(false)
                    },
                    modifier = Modifier.fillMaxWidth().heightIn(min = SolventaSpacing.minTouch),
                ) {
                    Text(option)
                }
            }
        }
    }
}
