package com.grupo8_uniandes.solventa.bff

import com.grupo8_uniandes.solventa.domain.bff.push.PushType
import com.grupo8_uniandes.solventa.domain.bff.push.pushTypeFrom
import com.grupo8_uniandes.solventa.domain.push.PushTarget
import com.grupo8_uniandes.solventa.domain.push.pushTargetFrom
import org.junit.Assert.assertEquals
import org.junit.Test

class PushTest {
    @Test
    fun givenEachKnownTipo_whenParsed_thenItMapsToThatPushType() {
        assertEquals(PushType.POLIZA_EMITIDA, pushTypeFrom("poliza_emitida"))
        assertEquals(PushType.POLIZA_RENOVADA, pushTypeFrom("poliza_renovada"))
        assertEquals(PushType.POLIZA_MODIFICADA, pushTypeFrom("poliza_modificada"))
        assertEquals(PushType.POLIZA_CANCELADA, pushTypeFrom("poliza_cancelada"))
        assertEquals(PushType.MENSAJE_OPERADOR, pushTypeFrom("mensaje_operador"))
    }

    @Test
    fun givenAnUnknownTipo_whenParsed_thenItIsDesconocido() {
        assertEquals(PushType.DESCONOCIDO, pushTypeFrom("otro"))
        assertEquals(PushType.DESCONOCIDO, pushTypeFrom(null))
        assertEquals(PushType.DESCONOCIDO, pushTypeFrom(""))
    }

    @Test
    fun givenADestination_whenParsed_thenPolizaDetalleNeedsAPolicyNumber() {
        assertEquals(
            PushTarget.PolizaDetalle("POL-2026-00000002"),
            pushTargetFrom("poliza-detalle", "POL-2026-00000002"),
        )
        assertEquals(PushTarget.Inicio, pushTargetFrom("poliza-detalle", null))
        assertEquals(PushTarget.Inicio, pushTargetFrom("poliza-detalle", "  "))
        assertEquals(PushTarget.Inicio, pushTargetFrom("inicio", "POL-2026-00000002"))
        assertEquals(PushTarget.Inicio, pushTargetFrom(null, null))
        assertEquals(PushTarget.Inicio, pushTargetFrom("aviso-vencimiento", "POL-1"))
    }
}
