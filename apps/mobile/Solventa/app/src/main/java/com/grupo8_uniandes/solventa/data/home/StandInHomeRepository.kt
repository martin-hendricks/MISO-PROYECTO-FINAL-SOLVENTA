package com.grupo8_uniandes.solventa.data.home

import com.grupo8_uniandes.solventa.data.bff.mock.MockHomeBffRepository
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.home.BffHome
import com.grupo8_uniandes.solventa.domain.bff.home.HomeBffRepository
import com.grupo8_uniandes.solventa.domain.home.ClaimCandidate
import com.grupo8_uniandes.solventa.domain.home.HomeRepository
import com.grupo8_uniandes.solventa.domain.home.HomeSituation
import com.grupo8_uniandes.solventa.domain.home.Origination
import com.grupo8_uniandes.solventa.domain.home.PolicyCandidate
import com.grupo8_uniandes.solventa.domain.home.Quote
import java.time.Instant

/**
 * The published home sample, as the situation Inicio already knows how to select.
 * A failed or pending stand-in answer is an empty home.
 */
class StandInHomeRepository(
    private val home: HomeBffRepository = MockHomeBffRepository(),
    private val becameCurrentAt: Instant = SAMPLE_AT,
) : HomeRepository {
    override fun load(): HomeSituation {
        val ready = home.load() as? StandInAnswer.Ready<BffHome> ?: return HomeSituation()
        val sample = ready.value
        return HomeSituation(
            quotes = listOf(
                Quote(
                    id = sample.ofertaVigente.cotizacionId,
                    consultable = sample.ofertaVigente.estado == IN_FORCE,
                    becameCurrentAt = becameCurrentAt,
                ),
            ),
            policies = listOf(
                PolicyCandidate(
                    id = sample.poliza.numero,
                    active = sample.poliza.estado == POLICY_IN_FORCE,
                    issuedAt = becameCurrentAt,
                ),
            ),
            claims = listOf(
                ClaimCandidate(
                    id = sample.siniestroEnCurso.siniestroId,
                    inProgress = sample.siniestroEnCurso.estado == CLAIM_IN_PROGRESS,
                    openedAt = becameCurrentAt,
                ),
            ),
            origination = Origination(present = sample.hipotecario != null),
        )
    }

    private companion object {
        val SAMPLE_AT: Instant = Instant.parse("2026-10-01T00:00:00Z")
        const val IN_FORCE = "oferta_vigente"
        const val POLICY_IN_FORCE = "vigente"
        const val CLAIM_IN_PROGRESS = "en_evaluacion"
    }
}
