package com.grupo8_uniandes.solventa.region

import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatRegionDate
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.LocalDate

class FormatRegionDateTest {
    @Test
    fun givenSeptember7_whenFormatted_thenEachRegionPattern() {
        val date = LocalDate.of(2026, 9, 7)

        assertEquals("09/07/2026", formatRegionDate(date, Region.Mexico))
        assertEquals("07/09/2026", formatRegionDate(date, Region.Colombia))
        assertEquals("07/09/2026", formatRegionDate(date, Region.Peru))
        assertEquals("07-09-2026", formatRegionDate(date, Region.Chile))
    }
}
