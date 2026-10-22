package com.grupo8_uniandes.solventa.login

import com.grupo8_uniandes.solventa.domain.login.DeviceUnlock
import com.grupo8_uniandes.solventa.domain.login.OpenHomeFromDeviceUnlock
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class DeviceUnlockTest {
    @Test
    fun givenAccepted_whenEvaluated_thenOpenHome() {
        val openHome = OpenHomeFromDeviceUnlock()

        assertTrue(openHome(DeviceUnlock.Accepted))
    }

    @Test
    fun givenDismissed_whenEvaluated_thenDoNotOpenHome() {
        assertFalse(OpenHomeFromDeviceUnlock()(DeviceUnlock.Dismissed))
    }

    @Test
    fun givenUnavailable_whenEvaluated_thenDoNotOpenHome() {
        assertFalse(OpenHomeFromDeviceUnlock()(DeviceUnlock.Unavailable))
    }
}
