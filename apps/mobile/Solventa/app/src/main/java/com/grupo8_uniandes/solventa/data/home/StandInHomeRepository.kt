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
import kotlinx.coroutines.runBlocking
import java.time.Instant

/**
 * The published home sample, as the situation Inicio already knows how to select.
 * A failed or pending stand-in answer is unavailable, not an empty home.
 */
class StandInHomeRepository(
    private val home: HomeBffRepository = MockHomeBffRepository(),
    private val becameCurrentAt: Instant = SAMPLE_AT,
) : HomeRepository {
    override fun load(): HomeSituation? {
        val ready = runBlocking { home.load() } as? StandInAnswer.Ready<BffHome> ?: return null
        val sample = ready.value
        return HomeSituation(
            quotes = sample.ofertaVigente?.let { offer ->
                listOf(
                Quote(
                    id = offer.cotizacionId,
                    consultable = offer.estado == IN_FORCE,
                    becameCurrentAt = becameCurrentAt,
                    ramo = offer.ramo,
                ),
                )
            }.orEmpty(),
            policies = sample.poliza?.let { policy ->
                listOf(
                    PolicyCandidate(
                        id = policy.numero,
                        active = policy.estado == POLICY_IN_FORCE,
                        issuedAt = becameCurrentAt,
                    ),
                )
            }.orEmpty(),
            claims = sample.siniestroEnCurso?.let { claim ->
                listOf(
                    ClaimCandidate(
                        id = claim.siniestroId,
                        inProgress = claim.estado == CLAIM_IN_PROGRESS,
                        openedAt = becameCurrentAt,
                    ),
                )
            }.orEmpty(),
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
