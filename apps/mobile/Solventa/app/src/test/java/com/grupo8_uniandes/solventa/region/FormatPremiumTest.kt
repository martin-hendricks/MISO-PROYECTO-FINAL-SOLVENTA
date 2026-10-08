package com.grupo8_uniandes.solventa.region

import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import org.junit.Assert.assertEquals
import org.junit.Test
import java.math.BigDecimal

class FormatPremiumTest {
    @Test
    fun givenMexico_whenAmountAndCodeArrive_thenChannelString() {
        val formatted = formatPremium(BigDecimal("1234.56"), "MXN", Region.Mexico)

        assertEquals("$1,234.56 MXN", formatted)
    }

    @Test
    fun givenSameAmountAndCode_whenRegionIsColombia_thenGroupingChangesAndValueStays() {
        val formatted = formatPremium(BigDecimal("1234.56"), "MXN", Region.Colombia)

        assertEquals("$1.234,56 MXN", formatted)
    }

    @Test
    fun givenCopAndClp_whenFormatted_thenZeroFractionDigits() {
        assertEquals(
            "$48.900 COP",
            formatPremium(BigDecimal("48900"), "COP", Region.Colombia),
        )
        assertEquals(
            "$48.900 CLP",
            formatPremium(BigDecimal("48900"), "CLP", Region.Chile),
        )
    }

    @Test
    fun givenPen_whenFormatted_thenSolSymbolAndTwoDigits() {
        assertEquals(
            "S/ 48.90 PEN",
            formatPremium(BigDecimal("48.90"), "PEN", Region.Peru),
        )
    }

    @Test
    fun givenUnknownCode_whenFormatted_thenNumberAndCodeWithoutInventedSymbol() {
        assertEquals(
            "10.00 USD",
            formatPremium(BigDecimal("10.00"), "USD", Region.Mexico),
        )
    }
}
