package com.grupo8_uniandes.solventa.accessibility

import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme

@Composable
fun AccessibleTheme(
    fontScale: Float = 1f,
    content: @Composable () -> Unit,
) {
    val base = LocalDensity.current
    CompositionLocalProvider(LocalDensity provides Density(base.density, fontScale)) {
        SolventaTheme(content = content)
    }
}
