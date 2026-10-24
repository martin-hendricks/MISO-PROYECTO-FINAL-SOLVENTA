package com.grupo8_uniandes.solventa.bff

import com.grupo8_uniandes.solventa.BuildConfig
import org.junit.Assert.assertEquals
import org.junit.Test

class DebugAddressTest {
    @Test
    fun debugUnitSuiteHasNoServiceAddress() {
        assertEquals("", BuildConfig.BFF_BASE_URL)
    }
}
