package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

enum class SolventaBannerStyle {
    Info,
    Error,
}

@Composable
fun SolventaBanner(
    message: String,
    style: SolventaBannerStyle,
    modifier: Modifier = Modifier,
) {
    val container = when (style) {
        SolventaBannerStyle.Info -> MaterialTheme.colorScheme.primaryContainer
        SolventaBannerStyle.Error -> MaterialTheme.colorScheme.errorContainer
    }
    val content = when (style) {
        SolventaBannerStyle.Info -> MaterialTheme.colorScheme.onPrimaryContainer
        SolventaBannerStyle.Error -> MaterialTheme.colorScheme.onErrorContainer
    }
    Surface(
        modifier = modifier.fillMaxWidth().testTag("solventa_banner_${style.name.lowercase()}"),
        color = container,
        contentColor = content,
        shape = SolventaSpacing.cardRadius,
    ) {
        Text(message, modifier = Modifier.padding(SolventaSpacing.gutter))
    }
}
