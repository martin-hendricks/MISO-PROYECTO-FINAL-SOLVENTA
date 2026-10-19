package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

enum class SolventaStatus {
    Success,
    Error,
    Processing,
}

@Composable
fun SolventaStatusIcon(
    status: SolventaStatus,
    word: String,
    icon: Painter,
    modifier: Modifier = Modifier,
) {
    val tint = when (status) {
        SolventaStatus.Success -> MaterialTheme.colorScheme.primary
        SolventaStatus.Error -> MaterialTheme.colorScheme.error
        SolventaStatus.Processing -> MaterialTheme.colorScheme.onSurfaceVariant
    }
    Row(
        modifier = modifier.testTag("solventa_status_${status.name.lowercase()}"),
        horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(painter = icon, contentDescription = null, tint = tint, modifier = Modifier.size(24.dp))
        Text(word, color = tint)
    }
}
