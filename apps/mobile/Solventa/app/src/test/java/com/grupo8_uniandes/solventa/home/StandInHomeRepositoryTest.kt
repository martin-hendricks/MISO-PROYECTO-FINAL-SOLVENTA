package com.grupo8_uniandes.solventa.home

import com.grupo8_uniandes.solventa.data.bff.dto.HomeDto
import com.grupo8_uniandes.solventa.data.bff.mapping.decode
import com.grupo8_uniandes.solventa.data.bff.mapping.required
import com.grupo8_uniandes.solventa.data.bff.mapping.toHome
import com.grupo8_uniandes.solventa.data.home.StandInHomeRepository
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.home.BffHome
import com.grupo8_uniandes.solventa.domain.bff.home.HomeBffRepository
import com.grupo8_uniandes.solventa.domain.bff.home.HomeClaimSlot
import com.grupo8_uniandes.solventa.domain.bff.home.HomeOfferSlot
import com.grupo8_uniandes.solventa.domain.bff.home.HomePolicySlot
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class StandInHomeRepositoryTest {
    @Test
    fun givenAFailedStandIn_whenLoaded_thenTheHomeIsUnavailable() {
        val repository = StandInHomeRepository(
            home = object : HomeBffRepository {
                override suspend fun load(): StandInAnswer<BffHome> = StandInAnswer.Failed
            },
        )

        assertNull(repository.load())
    }

    @Test
    fun givenOrigination_whenLoaded_thenVidaIsPresent() {
        val repository = StandInHomeRepository(
            home = object : HomeBffRepository {
                override suspend fun load(): StandInAnswer<BffHome> = StandInAnswer.Ready(
                    BffHome(
                        ofertaVigente = HomeOfferSlot("COT-1042", "Protección de dispositivo", "oferta_vigente"),
                        poliza = HomePolicySlot("POL-88219-CO", "Protección de dispositivo", "vigente"),
                        siniestroEnCurso = HomeClaimSlot("SIN-441", "en_evaluacion"),
                        hipotecario = "vida",
                    ),
                )
            },
        )

        assertEquals(true, repository.load()!!.origination.present)
    }

    @Test
    fun givenANullPolicy_whenLoaded_thenTheOfferAndClaimStay() {
        val situation = load(NULL_POLICY)

        assertEquals("COT-1042", situation.quotes.single().id)
        assertEquals("Protección de dispositivo", situation.quotes.single().ramo)
        assertTrue(situation.quotes.single().consultable)
        assertTrue(situation.policies.isEmpty())
        assertEquals("SIN-441", situation.claims.single().id)
        assertTrue(situation.claims.single().inProgress)
        assertFalse(situation.origination.present)
    }

    @Test
    fun givenEveryBlockNull_whenLoaded_thenTheHomeIsEmpty() {
        val situation = load(EMPTY_HOME)

        assertTrue(situation.quotes.isEmpty())
        assertTrue(situation.policies.isEmpty())
        assertTrue(situation.claims.isEmpty())
        assertFalse(situation.origination.present)
    }

    @Test
    fun givenInactiveSlots_whenLoaded_thenTheyStayButAreNotCurrent() {
        val situation = load(
            """
            {"ofertaVigente":{"cotizacionId":"COT-1","ramo":"Protección de dispositivo","estado":"vencida"},"poliza":{"numero":"POL-1","ramo":"Protección de dispositivo","estado":"cancelada"},"siniestroEnCurso":{"siniestroId":"SIN-1","estado":"pagado"},"hipotecario":null}
            """,
        )

        assertFalse(situation.quotes.single().consultable)
        assertFalse(situation.policies.single().active)
        assertFalse(situation.claims.single().inProgress)
    }

    private fun load(raw: String) = StandInHomeRepository(
        home = object : HomeBffRepository {
            override suspend fun load(): StandInAnswer<BffHome> =
                StandInAnswer.Ready(decode<HomeDto>(raw).let(::required).toHome())
        },
    ).load()!!

    private companion object {
        const val NULL_POLICY = """
            {"ofertaVigente":{"cotizacionId":"COT-1042","ramo":"Protección de dispositivo","estado":"oferta_vigente"},"poliza":null,"siniestroEnCurso":{"siniestroId":"SIN-441","estado":"en_evaluacion"},"hipotecario":null}
        """
        const val EMPTY_HOME = """
            {"ofertaVigente":null,"poliza":null,"siniestroEnCurso":null,"hipotecario":null}
        """
    }
}
