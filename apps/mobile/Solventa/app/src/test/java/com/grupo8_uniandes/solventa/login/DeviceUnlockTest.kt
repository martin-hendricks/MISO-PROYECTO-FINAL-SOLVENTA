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
    fun givenDismissedOrUnavailable_whenEvaluated_thenDoNotOpenHome() {
        val openHome = OpenHomeFromDeviceUnlock()

        assertFalse(openHome(DeviceUnlock.Dismissed))
        assertFalse(openHome(DeviceUnlock.Unavailable))
    }
}
