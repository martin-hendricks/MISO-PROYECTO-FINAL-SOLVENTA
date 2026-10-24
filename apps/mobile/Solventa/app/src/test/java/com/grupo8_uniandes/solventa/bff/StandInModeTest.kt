package com.grupo8_uniandes.solventa.bff

import com.grupo8_uniandes.solventa.data.bff.mapping.required
import com.grupo8_uniandes.solventa.data.bff.mock.MockOfferRepository
import com.grupo8_uniandes.solventa.data.bff.mock.StandInControl
import com.grupo8_uniandes.solventa.data.bff.mock.StandInMode
import com.grupo8_uniandes.solventa.data.bff.mock.publishedOfferRequest
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import kotlinx.serialization.SerializationException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import kotlinx.coroutines.runBlocking
import org.junit.Test

class StandInModeTest {
    private val risk = publishedOfferRequest()!!

    @Test
    fun givenFailureMode_whenQuote_thenTheSampleIsAbsent() {
        val offer = MockOfferRepository(StandInControl(StandInMode.Failure))

        val answer = runBlocking { offer.quote("Protección de dispositivo", risk) }

        assertTrue(answer is StandInAnswer.Failed)
    }

    @Test
    fun givenLateMode_whenReleased_thenTheSameSampleArrives() {
        val offer = MockOfferRepository(StandInControl(StandInMode.Late))

        assertTrue(runBlocking { offer.quote("Protección de dispositivo", risk) } is StandInAnswer.Pending)
        offer.release()
        val ready = runBlocking { offer.quote("Protección de dispositivo", risk) } as StandInAnswer.Ready

        assertEquals("COT-1042", ready.value.cotizacionId)
        assertEquals(89_000L, ready.value.prima)
        assertEquals("COP", ready.value.moneda)
    }

    @Test
    fun givenABrokenSample_whenTheStandInReadsIt_thenTheAnswerIsFailed() {
        val answer = StandInControl(StandInMode.Success).ready<String> { required(null) }

        assertTrue(answer is StandInAnswer.Failed)
    }
}
