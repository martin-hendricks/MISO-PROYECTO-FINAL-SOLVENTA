package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.width
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.FloatingActionButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.material3.contentColorFor
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.platform.testTag
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun SolventaFloatingAction(
    label: String,
    icon: Painter,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    containerColor: Color = FloatingActionButtonDefaults.containerColor,
    contentColor: Color = contentColorFor(containerColor),
) {
    ExtendedFloatingActionButton(
        onClick = onClick,
        modifier = modifier.testTag("solventa_floating_action"),
        containerColor = containerColor,
        contentColor = contentColor,
    ) {
        Icon(painter = icon, contentDescription = null)
        Spacer(Modifier.width(SolventaSpacing.s12))
        Text(label)
    }
}
