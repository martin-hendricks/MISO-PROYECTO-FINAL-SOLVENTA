package com.grupo8_uniandes.solventa.claim

import com.grupo8_uniandes.solventa.domain.bff.claim.OpenProviderCatalog
import com.grupo8_uniandes.solventa.domain.bff.claim.ProviderCatalog
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class OpenProviderCatalogTest {
    @Test
    fun givenLocationAllowed_whenTheCatalogOpens_thenTheStubIsNearerFirst() {
        val catalog = OpenProviderCatalog().open(locationAllowed = true) as ProviderCatalog.Open

        assertEquals("Taller Norte", catalog.rows[0].title)
        assertEquals("A 1,2 km · Chapinero", catalog.rows[0].body)
        assertEquals("En evaluación", catalog.rows[0].status)
        assertEquals("Taller Sur", catalog.rows[1].title)
        assertEquals("A 3,4 km · Kennedy", catalog.rows[1].body)
        assertEquals("Pagado", catalog.rows[1].status)
        assertEquals("SIN-P01", catalog.rows[2].title)
        assertEquals("Clima y vuelos · retraso de vuelo", catalog.rows[2].body)
        assertEquals("Pago automático · pagado", catalog.rows[2].status)
    }

    @Test
    fun givenLocationDenied_whenTheCatalogIsRequested_thenItStaysClosed() {
        val catalog = OpenProviderCatalog().open(locationAllowed = false)

        assertTrue(catalog is ProviderCatalog.Closed)
    }
}
