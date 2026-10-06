package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.platform.testTag

@Composable
fun SolventaFloatingAction(
    label: String,
    icon: Painter,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    ExtendedFloatingActionButton(
        onClick = onClick,
        modifier = modifier.testTag("solventa_floating_action"),
        icon = { Icon(painter = icon, contentDescription = null) },
        text = { Text(label) },
    )
}
