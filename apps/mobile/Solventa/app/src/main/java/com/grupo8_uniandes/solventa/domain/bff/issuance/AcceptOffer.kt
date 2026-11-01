package com.grupo8_uniandes.solventa.domain.bff.issuance

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import java.util.concurrent.atomic.AtomicBoolean

sealed interface AcceptOutcome {
    data object Ignored : AcceptOutcome

    data object Waiting : AcceptOutcome

    data object Unavailable : AcceptOutcome

    data class Issued(val policy: IssuedPolicy) : AcceptOutcome

    data class Refused(val rejection: IssueRejection) : AcceptOutcome
}

class AcceptOffer(
    private val issuance: IssuanceRepository,
) {
    private val active = AtomicBoolean(false)

    suspend fun accept(cotizacionId: String): AcceptOutcome {
        if (!active.compareAndSet(false, true)) return AcceptOutcome.Ignored
        return try {
            when (val answer = issuance.accept(cotizacionId)) {
                is StandInAnswer.Ready -> AcceptOutcome.Issued(answer.value)
                StandInAnswer.Pending -> AcceptOutcome.Waiting
                StandInAnswer.Failed -> when (val refusal = issuance.rejected()) {
                    is StandInAnswer.Ready -> AcceptOutcome.Refused(refusal.value)
                    else -> AcceptOutcome.Unavailable
                }
            }
        } finally {
            active.set(false)
        }
    }
}
