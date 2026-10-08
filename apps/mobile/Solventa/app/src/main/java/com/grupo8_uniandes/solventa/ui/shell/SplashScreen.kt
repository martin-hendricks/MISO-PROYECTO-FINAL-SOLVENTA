package com.grupo8_uniandes.solventa.ui.shell

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.core.view.WindowCompat
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.theme.HankenGrotesk
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.solventaLightColorScheme

internal const val SplashHoldMillis = 1_500L

private val splashWordmark = TextStyle(
    fontFamily = HankenGrotesk,
    fontWeight = FontWeight.SemiBold,
    fontSize = 40.sp,
    lineHeight = 40.sp,
)

private val splashTagline = TextStyle(
    fontFamily = HankenGrotesk,
    fontWeight = FontWeight.Normal,
    fontSize = 18.sp,
    lineHeight = 18.sp,
)

@Composable
fun SplashScreen(modifier: Modifier = Modifier) {
    val brand = solventaLightColorScheme()
    val view = LocalView.current
    DisposableEffect(view) {
        val activity = view.context.findActivity()
        if (activity == null) {
            onDispose { }
        } else {
            val controller = WindowCompat.getInsetsController(activity.window, view)
            val lightStatus = controller.isAppearanceLightStatusBars
            val lightNavigation = controller.isAppearanceLightNavigationBars
            controller.isAppearanceLightStatusBars = false
            controller.isAppearanceLightNavigationBars = false
            onDispose {
                controller.isAppearanceLightStatusBars = lightStatus
                controller.isAppearanceLightNavigationBars = lightNavigation
            }
        }
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(brand.primary)
            .testTag("screen_splash"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = stringResource(R.string.app_name),
            style = splashWordmark,
            color = brand.onPrimary,
        )
        Text(
            text = stringResource(R.string.splash_tagline),
            style = splashTagline,
            color = brand.onPrimaryContainer,
        )
    }
}

private fun Context.findActivity(): Activity? {
    var current: Context = this
    while (current is ContextWrapper) {
        if (current is Activity) return current
        current = current.baseContext
    }
    return null
}
