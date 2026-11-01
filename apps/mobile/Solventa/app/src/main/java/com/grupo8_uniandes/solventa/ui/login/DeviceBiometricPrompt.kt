package com.grupo8_uniandes.solventa.ui.login

import android.app.Activity
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import com.grupo8_uniandes.solventa.domain.login.DeviceUnlock

class DeviceBiometricPrompt(
    private val activity: Activity,
    private val title: String,
    private val negativeButtonText: String,
) {
    fun available(): Boolean = host() != null

    fun authenticate(onResult: (DeviceUnlock) -> Unit) {
        val fragmentActivity = host()
        if (fragmentActivity == null) {
            onResult(DeviceUnlock.Unavailable)
            return
        }
        val executor = ContextCompat.getMainExecutor(fragmentActivity)
        val prompt = BiometricPrompt(
            fragmentActivity,
            executor,
            DeviceUnlockCallback(onResult),
        )
        prompt.authenticate(
            BiometricPrompt.PromptInfo.Builder()
                .setTitle(title)
                .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_WEAK)
                .setNegativeButtonText(negativeButtonText)
                .build(),
        )
    }

    private fun host(): FragmentActivity? {
        val fragmentActivity = activity as? FragmentActivity ?: return null
        if (runningUnderInstrumentation()) return null
        val biometricManager = BiometricManager.from(fragmentActivity)
        val canAuthenticate = biometricManager.canAuthenticate(
            BiometricManager.Authenticators.BIOMETRIC_WEAK,
        )
        if (canAuthenticate != BiometricManager.BIOMETRIC_SUCCESS) return null
        return fragmentActivity
    }
}

internal class DeviceUnlockCallback(
    private val onResult: (DeviceUnlock) -> Unit,
) : BiometricPrompt.AuthenticationCallback() {
    private var completed = false

    override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
        if (completed) return
        completed = true
        onResult(DeviceUnlock.Accepted)
    }

    override fun onAuthenticationFailed() {
        if (completed) return
        completed = true
        onResult(DeviceUnlock.Dismissed)
    }

    override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
        if (completed) return
        completed = true
        onResult(DeviceUnlock.Dismissed)
    }
}

internal fun skipsBiometricPrompt(instrumentationClassName: String?): Boolean =
    instrumentationClassName != null && instrumentationClassName != "android.app.Instrumentation"

internal var instrumentationClassName: () -> String? = ::readInstrumentationClassName

internal fun runningUnderInstrumentation(): Boolean {
    return try {
        skipsBiometricPrompt(instrumentationClassName())
    } catch (_: Throwable) {
        false
    }
}

internal fun readInstrumentationClassName(): String? {
    val activityThreadClass = Class.forName("android.app.ActivityThread")
    val thread = activityThreadClass.getMethod("currentActivityThread").invoke(null) ?: return null
    val instrumentation = activityThreadClass.getMethod("getInstrumentation").invoke(thread) ?: return null
    return instrumentation.javaClass.name
}
