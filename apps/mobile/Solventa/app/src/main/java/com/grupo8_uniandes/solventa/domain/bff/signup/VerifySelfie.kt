package com.grupo8_uniandes.solventa.domain.bff.signup

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

enum class RecordStep {
    Check,
    Record,
}

sealed interface SelfieOutcome {
    data object Passed : SelfieOutcome

    data object Failed : SelfieOutcome

    data class Unavailable(val step: RecordStep) : SelfieOutcome
}

class VerifySelfie(
    private val liveness: LivenessRepository,
) {
    suspend operator fun invoke(photo: ByteArray): SelfieOutcome =
        when (liveness.check(photo)) {
            LivenessCheck.Failed -> SelfieOutcome.Failed
            LivenessCheck.Unavailable -> SelfieOutcome.Unavailable(RecordStep.Check)
            LivenessCheck.Passed -> record()
        }

    suspend fun retryRecord(): SelfieOutcome = record()

    private suspend fun record(): SelfieOutcome =
        when (liveness.record(Liveness.OK)) {
            is StandInAnswer.Ready -> SelfieOutcome.Passed
            else -> SelfieOutcome.Unavailable(RecordStep.Record)
        }
}
