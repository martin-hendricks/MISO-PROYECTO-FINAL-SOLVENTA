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
    fun authenticate(onResult: (DeviceUnlock) -> Unit) {
        val fragmentActivity = activity as? FragmentActivity
        if (fragmentActivity == null) {
            onResult(DeviceUnlock.Unavailable)
            return
        }
        val biometricManager = BiometricManager.from(fragmentActivity)
        if (biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_WEAK) != BiometricManager.BIOMETRIC_SUCCESS) {
            onResult(DeviceUnlock.Unavailable)
            return
        }
        val executor = ContextCompat.getMainExecutor(fragmentActivity)
        var completed = false
        val prompt = BiometricPrompt(
            fragmentActivity,
            executor,
            object : BiometricPrompt.AuthenticationCallback() {
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
            },
        )
        prompt.authenticate(
            BiometricPrompt.PromptInfo.Builder()
                .setTitle(title)
                .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_WEAK)
                .setNegativeButtonText(negativeButtonText)
                .build(),
        )
    }
}
