package com.grupo8_uniandes.solventa.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable

@Composable
fun SolventaTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) solventaDarkColorScheme() else solventaLightColorScheme(),
        typography = SolventaTypography.material,
        content = content,
    )
}
