package com.grupo8_uniandes.solventa.domain.consent

open class ChangeDataTreatment(
    private val repository: ConsentRepository,
    private val now: () -> Long,
) {
    open fun grant(): ConsentSnapshot = apply(ConsentAction.Grant, ConsentState.Granted)

    open fun revoke(): ConsentSnapshot = apply(ConsentAction.Revoke, ConsentState.Revoked)

    private fun apply(action: ConsentAction, resulting: ConsentState): ConsentSnapshot {
        val current = repository.read()
        val allowed = when (action) {
            ConsentAction.Grant -> current.state != ConsentState.Granted
            ConsentAction.Revoke -> current.state == ConsentState.Granted
        }
        if (!allowed) return current
        repository.append(
            ConsentRecord(
                action = action,
                atMillis = now(),
                resulting = resulting,
            ),
        )
        return repository.read()
    }
}
