package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.platform.testTag
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

enum class SolventaIconButtonStyle {
    Default,
    OnSurface,
}

@Composable
fun SolventaIconButton(
    icon: Painter,
    contentDescription: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    style: SolventaIconButtonStyle = SolventaIconButtonStyle.Default,
    testTag: String = "solventa_icon_button",
) {
    val tint = when (style) {
        SolventaIconButtonStyle.Default -> MaterialTheme.colorScheme.onSurfaceVariant
        SolventaIconButtonStyle.OnSurface -> MaterialTheme.colorScheme.onSurface
    }
    IconButton(
        onClick = onClick,
        modifier = modifier.size(SolventaSpacing.minTouch).testTag(testTag),
    ) {
        Icon(painter = icon, contentDescription = contentDescription, tint = tint)
    }
}
