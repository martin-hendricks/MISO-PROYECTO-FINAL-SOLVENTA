package com.grupo8_uniandes.solventa.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.grupo8_uniandes.solventa.R

val HankenGrotesk = FontFamily(
    Font(R.font.hanken_grotesk_regular, FontWeight.Normal),
    Font(R.font.hanken_grotesk_medium, FontWeight.Medium),
    Font(R.font.hanken_grotesk_semibold, FontWeight.SemiBold),
)

val JetBrainsMono = FontFamily(
    Font(R.font.jet_brains_mono_medium, FontWeight.Medium),
)

private fun hanken(weight: FontWeight, size: Int, lineHeight: Int) = TextStyle(
    fontFamily = HankenGrotesk,
    fontWeight = weight,
    fontSize = size.sp,
    lineHeight = lineHeight.sp,
)

object SolventaTypography {
    val material = Typography(
        headlineMedium = hanken(FontWeight.SemiBold, 28, 36),
        headlineSmall = hanken(FontWeight.Medium, 24, 32),
        titleMedium = hanken(FontWeight.Medium, 16, 24),
        bodyLarge = hanken(FontWeight.Normal, 16, 24),
        bodyMedium = hanken(FontWeight.Normal, 14, 20),
    )

    val amount = TextStyle(
        fontFamily = JetBrainsMono,
        fontWeight = FontWeight.Medium,
        fontSize = 12.sp,
        lineHeight = 16.sp,
    )
}
