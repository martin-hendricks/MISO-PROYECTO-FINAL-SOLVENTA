package com.grupo8_uniandes.solventa

import android.content.Context
import android.content.Intent
import android.content.res.Configuration
import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.fragment.app.FragmentActivity
import com.grupo8_uniandes.solventa.data.region.readAppliedLanguageTag
import com.grupo8_uniandes.solventa.domain.push.PushTarget
import com.grupo8_uniandes.solventa.domain.push.pushTargetFrom
import com.grupo8_uniandes.solventa.domain.startup.StartupSession
import com.grupo8_uniandes.solventa.ui.shell.CustomerShell
import com.grupo8_uniandes.solventa.ui.shell.SplashHoldMillis
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import java.util.Locale

class MainActivity : FragmentActivity() {
    private var pushTarget by mutableStateOf<PushTarget?>(null)
    internal var deliveredPush: PushTarget? = null
        private set
    internal val pendingPush: PushTarget?
        get() = pushTarget

    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(newBase.withAppliedRegion())
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        pushTarget = savedInstanceState?.readPushTarget()
        consumePushIntent(intent)
        val splashHoldMillis = intent.getLongExtra(EXTRA_SPLASH_HOLD_MILLIS, SplashHoldMillis)
        val startupSession = if (intent.getBooleanExtra(EXTRA_EXISTING_ACCOUNT, false)) {
            StartupSession.ExistingAccount
        } else {
            StartupSession.FirstUse
        }
        val enterSignedInShell = intent.getBooleanExtra(EXTRA_ENTER_SIGNED_IN_SHELL, false)
        val openHome = intent.getBooleanExtra(EXTRA_OPEN_HOME, false)
        val openOnboarding = intent.getBooleanExtra(EXTRA_OPEN_ONBOARDING, false)
        val onboardingShowsStep = intent.getBooleanExtra(EXTRA_ONBOARDING_STEP, true)
        val openLiveness = intent.getBooleanExtra(EXTRA_OPEN_LIVENESS, false)
        val openConsent = intent.getBooleanExtra(EXTRA_OPEN_CONSENT, false)
        val resumeProfile = intent.getBooleanExtra(EXTRA_RESUME_PROFILE, false)
        val signedOut = intent.getBooleanExtra(EXTRA_SIGNED_OUT, false)
        val askPush = intent.getBooleanExtra(EXTRA_ASK_PUSH, false)
        if (openHome) {
            intent.removeExtra(EXTRA_OPEN_HOME)
        }
        if (openOnboarding) {
            intent.removeExtra(EXTRA_OPEN_ONBOARDING)
            intent.removeExtra(EXTRA_ONBOARDING_STEP)
        }
        if (openLiveness) {
            intent.removeExtra(EXTRA_OPEN_LIVENESS)
        }
        if (openConsent) {
            intent.removeExtra(EXTRA_OPEN_CONSENT)
        }
        if (resumeProfile) {
            intent.removeExtra(EXTRA_RESUME_PROFILE)
        }
        if (askPush) {
            intent.removeExtra(EXTRA_ASK_PUSH)
        }
        setContent {
            SolventaTheme {
                CustomerShell(
                    startupSession = startupSession,
                    splashHoldMillis = splashHoldMillis,
                    enterSignedInShell = enterSignedInShell || openHome,
                    openOnboarding = openOnboarding,
                    onboardingShowsStep = onboardingShowsStep,
                    openLiveness = openLiveness,
                    openConsent = openConsent,
                    resumeProfile = resumeProfile,
                    signedOut = signedOut,
                    askPush = askPush,
                    pushTarget = pushTarget,
                    onPushHandled = { pushTarget = null },
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        consumePushIntent(intent)
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        when (val target = pushTarget) {
            is PushTarget.PolizaDetalle -> {
                outState.putString(STATE_PUSH_DESTINO, "poliza-detalle")
                outState.putString(STATE_PUSH_POLIZA, target.numero)
            }
            PushTarget.Inicio -> outState.putString(STATE_PUSH_DESTINO, "inicio")
            null -> Unit
        }
    }

    private fun consumePushIntent(source: Intent?) {
        if (source == null) return
        val destino = source.getStringExtra(EXTRA_PUSH_DESTINO) ?: source.getStringExtra("destino")
        val poliza = source.getStringExtra(EXTRA_PUSH_POLIZA) ?: source.getStringExtra("poliza")
        if (destino == null && poliza == null) return
        val target = pushTargetFrom(destino, poliza)
        deliveredPush = target
        pushTarget = target
        source.removeExtra(EXTRA_PUSH_DESTINO)
        source.removeExtra(EXTRA_PUSH_POLIZA)
        source.removeExtra("destino")
        source.removeExtra("poliza")
    }

    companion object {
        const val EXTRA_SPLASH_HOLD_MILLIS = "com.grupo8_uniandes.solventa.SPLASH_HOLD_MILLIS"
        const val EXTRA_EXISTING_ACCOUNT = "com.grupo8_uniandes.solventa.EXISTING_ACCOUNT"
        const val EXTRA_ENTER_SIGNED_IN_SHELL = "com.grupo8_uniandes.solventa.ENTER_SIGNED_IN_SHELL"
        const val EXTRA_OPEN_HOME = "com.grupo8_uniandes.solventa.OPEN_HOME"
        const val EXTRA_OPEN_ONBOARDING = "com.grupo8_uniandes.solventa.OPEN_ONBOARDING"
        const val EXTRA_ONBOARDING_STEP = "com.grupo8_uniandes.solventa.ONBOARDING_STEP"
        const val EXTRA_OPEN_LIVENESS = "com.grupo8_uniandes.solventa.OPEN_LIVENESS"
        const val EXTRA_OPEN_CONSENT = "com.grupo8_uniandes.solventa.OPEN_CONSENT"
        const val EXTRA_RESUME_PROFILE = "com.grupo8_uniandes.solventa.RESUME_PROFILE"
        const val EXTRA_SIGNED_OUT = "com.grupo8_uniandes.solventa.SIGNED_OUT"
        const val EXTRA_ASK_PUSH = "com.grupo8_uniandes.solventa.ASK_PUSH"
        const val EXTRA_PUSH_DESTINO = "com.grupo8_uniandes.solventa.PUSH_DESTINO"
        const val EXTRA_PUSH_POLIZA = "com.grupo8_uniandes.solventa.PUSH_POLIZA"

        internal const val STATE_PUSH_DESTINO = "com.grupo8_uniandes.solventa.STATE_PUSH_DESTINO"
        internal const val STATE_PUSH_POLIZA = "com.grupo8_uniandes.solventa.STATE_PUSH_POLIZA"
    }
}

private fun Bundle.readPushTarget(): PushTarget? {
    if (!containsKey(MainActivity.STATE_PUSH_DESTINO)) return null
    return pushTargetFrom(
        getString(MainActivity.STATE_PUSH_DESTINO),
        getString(MainActivity.STATE_PUSH_POLIZA),
    )
}

private fun Context.withAppliedRegion(): Context {
    val locale = Locale.forLanguageTag(readAppliedLanguageTag(this))
    val config = Configuration(resources.configuration)
    config.setLocale(locale)
    return createConfigurationContext(config)
}
