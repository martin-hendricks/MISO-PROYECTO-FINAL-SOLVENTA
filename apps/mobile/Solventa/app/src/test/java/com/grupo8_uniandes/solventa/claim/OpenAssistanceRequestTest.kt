package com.grupo8_uniandes.solventa.claim

import com.grupo8_uniandes.solventa.domain.bff.claim.OpenAssistanceRequest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class OpenAssistanceRequestTest {
    @Test
    fun givenLocationAllowed_whenAssistanceOpens_thenTheFrameValuesArePresent() {
        val form = OpenAssistanceRequest().open(locationAllowed = true)!!

        assertEquals(
            "Registramos el pedido con tu ubicación. Operaciones lo ve; no hay despacho real a un taller.",
            form.registration,
        )
        assertEquals("POL-88219-CO · Protección de dispositivo", form.policyValue)
        assertEquals("12 mar 2026", form.dateValue)
        assertEquals("Pantalla rota al caer el teléfono", form.descriptionValue)
        assertEquals("Av. Caracas con Calle 72", form.placeValue)
    }

    @Test
    fun givenACancel_whenRecorded_thenASecondRequestIsNotStarted() {
        val request = OpenAssistanceRequest()
        request.open(locationAllowed = true)
        request.cancel()

        assertEquals(1, request.openedCount())
        assertNull(request.open(locationAllowed = true))
    }

    @Test
    fun givenLocationDenied_whenAssistanceIsRequested_thenItDoesNotOpen() {
        assertNull(OpenAssistanceRequest().open(locationAllowed = false))
    }
}
