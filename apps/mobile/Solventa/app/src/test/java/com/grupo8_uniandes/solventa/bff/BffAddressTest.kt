package com.grupo8_uniandes.solventa.bff

import com.grupo8_uniandes.solventa.data.bff.BffAddress
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BffAddressTest {
    @Test
    fun givenNoAddress_whenResolved_thenItIsEmpty() {
        assertEquals("", BffAddress.resolve(null, null))
        assertEquals("", BffAddress.resolve("  ", ""))
    }

    @Test
    fun givenAGradleAddress_whenLocalIsAlsoSet_thenGradleWins() {
        assertEquals(
            "https://edge.example",
            BffAddress.resolve(" https://edge.example ", "http://10.0.2.2:8080"),
        )
    }

    @Test
    fun givenABlankGradleAddress_whenLocalIsSet_thenLocalIsUsed() {
        assertEquals("http://10.0.2.2:8080", BffAddress.resolve(" ", "http://10.0.2.2:8080"))
    }

    @Test
    fun givenAnHttpAddress_whenCleartextIsDecided_thenOnlyHttpIsAllowed() {
        assertTrue(BffAddress.allowsCleartext("http://10.0.2.2:8080"))
        assertFalse(BffAddress.allowsCleartext("https://edge.example"))
        assertFalse(BffAddress.allowsCleartext(""))
    }
}
