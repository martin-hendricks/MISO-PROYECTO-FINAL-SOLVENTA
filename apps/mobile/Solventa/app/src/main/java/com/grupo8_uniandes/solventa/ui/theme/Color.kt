package com.grupo8_uniandes.solventa.ui.theme

import androidx.compose.material3.ColorScheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color

private val LightPrimary = Color(0xFF005050)
private val LightOnPrimary = Color(0xFFFFFFFF)
private val LightPrimaryContainer = Color(0xFF006A6A)
private val LightOnPrimaryContainer = Color(0xFF97E7E6)
private val LightSecondaryContainer = Color(0xFFCCE8E7)
private val LightOnSecondaryContainer = Color(0xFF506969)
private val LightSurface = Color(0xFFF7FAF9)
private val LightOnSurface = Color(0xFF181C1C)
private val LightOnSurfaceVariant = Color(0xFF3E4948)
private val LightSurfaceContainerLow = Color(0xFFF1F4F4)
private val LightSurfaceContainerLowest = Color(0xFFFFFFFF)
private val LightOutline = Color(0xFF6E7979)
private val LightOutlineVariant = Color(0xFFBEC9C8)
private val LightError = Color(0xFFBA1A1A)
private val LightErrorContainer = Color(0xFFFFDAD6)

private val DarkPrimary = Color(0xFF84D4D3)
private val DarkOnPrimary = Color(0xFF003737)
private val DarkPrimaryContainer = Color(0xFF004F4F)
private val DarkOnPrimaryContainer = Color(0xFFA0F0F0)
private val DarkSecondaryContainer = Color(0xFF324B4B)
private val DarkOnSecondaryContainer = Color(0xFFCCE8E7)
private val DarkSurface = Color(0xFF101414)
private val DarkOnSurface = Color(0xFFE0E3E3)
private val DarkOnSurfaceVariant = Color(0xFFBEC9C8)
private val DarkSurfaceContainerLow = Color(0xFF191C1C)
private val DarkSurfaceContainerLowest = Color(0xFF0C0F0F)
private val DarkOutline = Color(0xFF889392)
private val DarkOutlineVariant = Color(0xFF3E4948)
private val DarkError = Color(0xFFFFB4AB)
private val DarkErrorContainer = Color(0xFF93000A)

fun solventaLightColorScheme(): ColorScheme = lightColorScheme(
    primary = LightPrimary,
    onPrimary = LightOnPrimary,
    primaryContainer = LightPrimaryContainer,
    onPrimaryContainer = LightOnPrimaryContainer,
    secondaryContainer = LightSecondaryContainer,
    onSecondaryContainer = LightOnSecondaryContainer,
    surface = LightSurface,
    onSurface = LightOnSurface,
    onSurfaceVariant = LightOnSurfaceVariant,
    surfaceContainerLow = LightSurfaceContainerLow,
    surfaceContainerLowest = LightSurfaceContainerLowest,
    outline = LightOutline,
    outlineVariant = LightOutlineVariant,
    error = LightError,
    errorContainer = LightErrorContainer,
    background = LightSurface,
    onBackground = LightOnSurface,
)

fun solventaDarkColorScheme(): ColorScheme = darkColorScheme(
    primary = DarkPrimary,
    onPrimary = DarkOnPrimary,
    primaryContainer = DarkPrimaryContainer,
    onPrimaryContainer = DarkOnPrimaryContainer,
    secondaryContainer = DarkSecondaryContainer,
    onSecondaryContainer = DarkOnSecondaryContainer,
    surface = DarkSurface,
    onSurface = DarkOnSurface,
    onSurfaceVariant = DarkOnSurfaceVariant,
    surfaceContainerLow = DarkSurfaceContainerLow,
    surfaceContainerLowest = DarkSurfaceContainerLowest,
    outline = DarkOutline,
    outlineVariant = DarkOutlineVariant,
    error = DarkError,
    errorContainer = DarkErrorContainer,
    background = DarkSurface,
    onBackground = DarkOnSurface,
)
