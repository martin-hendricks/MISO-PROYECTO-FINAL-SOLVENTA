package com.grupo8_uniandes.solventa.ui.theme

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class SolventaColorSchemeTest {
    @Test
    fun lightPairsMatchTheDesignContract() {
        val scheme = solventaLightColorScheme()
        assertEquals(Color(0xFF005050), scheme.primary)
        assertEquals(Color(0xFFFFFFFF), scheme.onPrimary)
        assertEquals(Color(0xFF006A6A), scheme.primaryContainer)
        assertEquals(Color(0xFF97E7E6), scheme.onPrimaryContainer)
        assertEquals(Color(0xFFCCE8E7), scheme.secondaryContainer)
        assertEquals(Color(0xFF506969), scheme.onSecondaryContainer)
        assertEquals(Color(0xFFF7FAF9), scheme.surface)
        assertEquals(Color(0xFF181C1C), scheme.onSurface)
        assertEquals(Color(0xFF3E4948), scheme.onSurfaceVariant)
        assertEquals(Color(0xFFF1F4F4), scheme.surfaceContainerLow)
        assertEquals(Color(0xFFFFFFFF), scheme.surfaceContainerLowest)
        assertEquals(Color(0xFF6E7979), scheme.outline)
        assertEquals(Color(0xFFBEC9C8), scheme.outlineVariant)
        assertEquals(Color(0xFFBA1A1A), scheme.error)
        assertEquals(Color(0xFFFFDAD6), scheme.errorContainer)
    }

    @Test
    fun darkPairsMatchTheDesignContract() {
        val scheme = solventaDarkColorScheme()
        assertEquals(Color(0xFF84D4D3), scheme.primary)
        assertEquals(Color(0xFF003737), scheme.onPrimary)
        assertEquals(Color(0xFF004F4F), scheme.primaryContainer)
        assertEquals(Color(0xFFA0F0F0), scheme.onPrimaryContainer)
        assertEquals(Color(0xFF324B4B), scheme.secondaryContainer)
        assertEquals(Color(0xFFCCE8E7), scheme.onSecondaryContainer)
        assertEquals(Color(0xFF101414), scheme.surface)
        assertEquals(Color(0xFFE0E3E3), scheme.onSurface)
        assertEquals(Color(0xFFBEC9C8), scheme.onSurfaceVariant)
        assertEquals(Color(0xFF191C1C), scheme.surfaceContainerLow)
        assertEquals(Color(0xFF0C0F0F), scheme.surfaceContainerLowest)
        assertEquals(Color(0xFF889392), scheme.outline)
        assertEquals(Color(0xFF3E4948), scheme.outlineVariant)
        assertEquals(Color(0xFFFFB4AB), scheme.error)
        assertEquals(Color(0xFF93000A), scheme.errorContainer)
    }

    @Test
    fun amountUsesJetBrainsMonoNotHankenGrotesk() {
        assertEquals(12.sp, SolventaTypography.amount.fontSize)
        assertEquals(16.sp, SolventaTypography.amount.lineHeight)
        assertEquals(FontWeight.Medium, SolventaTypography.amount.fontWeight)
        assertEquals(JetBrainsMono, SolventaTypography.amount.fontFamily)
        assertNotEquals(HankenGrotesk, SolventaTypography.amount.fontFamily)
        assertEquals(28.sp, SolventaTypography.material.headlineMedium.fontSize)
        assertEquals(36.sp, SolventaTypography.material.headlineMedium.lineHeight)
        assertEquals(FontWeight.SemiBold, SolventaTypography.material.headlineMedium.fontWeight)
        assertEquals(HankenGrotesk, SolventaTypography.material.headlineMedium.fontFamily)
    }
}
