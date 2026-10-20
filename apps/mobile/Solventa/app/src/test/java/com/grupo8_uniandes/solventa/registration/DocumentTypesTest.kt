package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.registration.documentTypes
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class DocumentTypesTest {
    @Test
    fun givenEachRegion_whenListed_thenOnlyAdultTypes() {
        assertEquals(listOf("CC", "CE", "PA"), documentTypes(Region.Colombia))
        assertEquals(listOf("INE", "CURP", "PA"), documentTypes(Region.Mexico))
        assertEquals(listOf("RUT", "PA"), documentTypes(Region.Chile))
        assertEquals(listOf("DNI", "CE", "PA"), documentTypes(Region.Peru))
        assertFalse("TI" in documentTypes(Region.Colombia))
        assertFalse("RC" in documentTypes(Region.Colombia))
    }
}
