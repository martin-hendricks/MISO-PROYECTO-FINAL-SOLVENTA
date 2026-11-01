package com.grupo8_uniandes.solventa.home

import com.grupo8_uniandes.solventa.data.home.StandInHomeRepository
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.home.BffHome
import com.grupo8_uniandes.solventa.domain.bff.home.HomeBffRepository
import com.grupo8_uniandes.solventa.domain.bff.home.HomeClaimSlot
import com.grupo8_uniandes.solventa.domain.bff.home.HomeOfferSlot
import com.grupo8_uniandes.solventa.domain.bff.home.HomePolicySlot
import org.junit.Assert.assertEquals
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
}
