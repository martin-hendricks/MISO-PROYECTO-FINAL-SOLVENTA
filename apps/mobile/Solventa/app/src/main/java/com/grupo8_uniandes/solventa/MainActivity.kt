package com.grupo8_uniandes.solventa

import android.content.Context
import android.content.res.Configuration
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.grupo8_uniandes.solventa.data.region.readAppliedLanguageTag
import com.grupo8_uniandes.solventa.domain.startup.StartupSession
import com.grupo8_uniandes.solventa.ui.shell.CustomerShell
import com.grupo8_uniandes.solventa.ui.shell.SplashHoldMillis
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import java.util.Locale

class MainActivity : ComponentActivity() {
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(newBase.withAppliedRegion())
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val splashHoldMillis = intent.getLongExtra(EXTRA_SPLASH_HOLD_MILLIS, SplashHoldMillis)
        val startupSession = if (intent.getBooleanExtra(EXTRA_EXISTING_ACCOUNT, false)) {
            StartupSession.ExistingAccount
        } else {
            StartupSession.FirstUse
        }
        val enterSignedInShell = intent.getBooleanExtra(EXTRA_ENTER_SIGNED_IN_SHELL, false)
        val openHome = intent.getBooleanExtra(EXTRA_OPEN_HOME, false)
        val resumeProfile = intent.getBooleanExtra(EXTRA_RESUME_PROFILE, false)
        if (openHome) {
            intent.removeExtra(EXTRA_OPEN_HOME)
        }
        if (resumeProfile) {
            intent.removeExtra(EXTRA_RESUME_PROFILE)
        }
        setContent {
            SolventaTheme {
                CustomerShell(
                    startupSession = startupSession,
                    splashHoldMillis = splashHoldMillis,
                    enterSignedInShell = enterSignedInShell || openHome,
                    resumeProfile = resumeProfile,
                )
            }
        }
    }

    companion object {
        const val EXTRA_SPLASH_HOLD_MILLIS = "com.grupo8_uniandes.solventa.SPLASH_HOLD_MILLIS"
        const val EXTRA_EXISTING_ACCOUNT = "com.grupo8_uniandes.solventa.EXISTING_ACCOUNT"
        const val EXTRA_ENTER_SIGNED_IN_SHELL = "com.grupo8_uniandes.solventa.ENTER_SIGNED_IN_SHELL"
        const val EXTRA_OPEN_HOME = "com.grupo8_uniandes.solventa.OPEN_HOME"
        const val EXTRA_RESUME_PROFILE = "com.grupo8_uniandes.solventa.RESUME_PROFILE"
    }
}

private fun Context.withAppliedRegion(): Context {
    val locale = Locale.forLanguageTag(readAppliedLanguageTag(this))
    val config = Configuration(resources.configuration)
    config.setLocale(locale)
    return createConfigurationContext(config)
}
