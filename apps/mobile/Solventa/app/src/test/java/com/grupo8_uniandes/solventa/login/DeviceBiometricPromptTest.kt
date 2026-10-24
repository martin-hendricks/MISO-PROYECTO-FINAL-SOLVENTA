package com.grupo8_uniandes.solventa.login

import android.app.Activity
import androidx.biometric.BiometricPrompt
import androidx.fragment.app.FragmentActivity
import com.grupo8_uniandes.solventa.domain.login.DeviceUnlock
import com.grupo8_uniandes.solventa.ui.login.DeviceBiometricPrompt
import com.grupo8_uniandes.solventa.ui.login.DeviceUnlockCallback
import com.grupo8_uniandes.solventa.ui.login.instrumentationClassName
import com.grupo8_uniandes.solventa.ui.login.readInstrumentationClassName
import com.grupo8_uniandes.solventa.ui.login.runningUnderInstrumentation
import com.grupo8_uniandes.solventa.ui.login.skipsBiometricPrompt
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

class DeviceBiometricPromptDecisionTest {
    @Test
    fun givenClassName_whenChecked_thenOnlyANonDefaultInstrumentationSkips() {
        assertFalse(skipsBiometricPrompt(null))
        assertFalse(skipsBiometricPrompt("android.app.Instrumentation"))
        assertTrue(skipsBiometricPrompt("androidx.test.runner.AndroidJUnitRunner"))
    }

    @Test
    fun givenNoActivityThread_whenChecked_thenThePromptIsNotSkipped() {
        assertFalse(runningUnderInstrumentation())
    }

    @Test
    fun givenLookupThrows_whenChecked_thenThePromptIsNotSkipped() {
        val previous = instrumentationClassName
        instrumentationClassName = { throw IllegalStateException("lookup") }
        try {
            assertFalse(runningUnderInstrumentation())
        } finally {
            instrumentationClassName = previous
        }
    }
}

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28])
class DeviceBiometricPromptTest {
    @After
    fun restoreLookup() {
        instrumentationClassName = ::readInstrumentationClassName
    }

    @Test
    fun givenPlainActivity_whenAuthenticate_thenUnavailable() {
        val activity = Robolectric.buildActivity(Activity::class.java).setup().get()
        val results = mutableListOf<DeviceUnlock>()

        DeviceBiometricPrompt(activity, "Huella o rostro", "Cancelar").authenticate(results::add)

        assertEquals(listOf(DeviceUnlock.Unavailable), results)
    }

    @Test
    fun givenInstrumentedFragment_whenAuthenticate_thenUnavailableWithoutAPrompt() {
        val activity = Robolectric.buildActivity(FragmentActivity::class.java).setup().get()
        val results = mutableListOf<DeviceUnlock>()

        assertTrue(runningUnderInstrumentation())
        DeviceBiometricPrompt(activity, "Huella o rostro", "Cancelar").authenticate(results::add)

        assertEquals(listOf(DeviceUnlock.Unavailable), results)
    }

    @Test
    fun givenDefaultInstrumentation_whenTheDeviceCannotAuthenticate_thenUnavailable() {
        instrumentationClassName = { "android.app.Instrumentation" }
        val activity = Robolectric.buildActivity(FragmentActivity::class.java).setup().get()
        val results = mutableListOf<DeviceUnlock>()

        assertFalse(runningUnderInstrumentation())
        DeviceBiometricPrompt(activity, "Huella o rostro", "Cancelar").authenticate(results::add)

        assertEquals(listOf(DeviceUnlock.Unavailable), results)
    }

    @Test
    fun givenCallback_whenEachResultArrivesTwice_thenOnlyTheFirstIsReported() {
        val results = mutableListOf<DeviceUnlock>()
        val callback = DeviceUnlockCallback(results::add)
        val success = authenticationResult()

        callback.onAuthenticationSucceeded(success)
        callback.onAuthenticationSucceeded(success)
        assertEquals(listOf(DeviceUnlock.Accepted), results)

        val failed = DeviceUnlockCallback(results::add)
        results.clear()
        failed.onAuthenticationFailed()
        failed.onAuthenticationFailed()
        assertEquals(listOf(DeviceUnlock.Dismissed), results)

        val error = DeviceUnlockCallback(results::add)
        results.clear()
        error.onAuthenticationError(BiometricPrompt.ERROR_CANCELED, "cancel")
        error.onAuthenticationError(BiometricPrompt.ERROR_CANCELED, "cancel")
        assertEquals(listOf(DeviceUnlock.Dismissed), results)
    }
}

private fun authenticationResult(): BiometricPrompt.AuthenticationResult {
    val constructor = BiometricPrompt.AuthenticationResult::class.java.declaredConstructors.first()
    constructor.isAccessible = true
    return constructor.newInstance(null, 0) as BiometricPrompt.AuthenticationResult
}
