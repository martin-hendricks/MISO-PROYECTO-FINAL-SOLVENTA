package com.grupo8_uniandes.solventa

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.grupo8_uniandes.solventa.domain.startup.StartupSession
import com.grupo8_uniandes.solventa.ui.shell.CustomerShell
import com.grupo8_uniandes.solventa.ui.shell.SplashHoldMillis
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme

class MainActivity : ComponentActivity() {
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
        setContent {
            SolventaTheme {
                CustomerShell(
                    startupSession = startupSession,
                    splashHoldMillis = splashHoldMillis,
                    enterSignedInShell = enterSignedInShell,
                )
            }
        }
    }

    companion object {
        const val EXTRA_SPLASH_HOLD_MILLIS = "com.grupo8_uniandes.solventa.SPLASH_HOLD_MILLIS"
        const val EXTRA_EXISTING_ACCOUNT = "com.grupo8_uniandes.solventa.EXISTING_ACCOUNT"
        const val EXTRA_ENTER_SIGNED_IN_SHELL = "com.grupo8_uniandes.solventa.ENTER_SIGNED_IN_SHELL"
    }
}
