package com.grupo8_uniandes.solventa.domain.consent

interface ConsentRepository {
    fun read(): ConsentSnapshot

    /**
     * Appends one record when the transition is legal.
     * A grant is legal from [ConsentState.NotGranted] or [ConsentState.Revoked].
     * A revoke is legal only from [ConsentState.Granted].
     * A repeated confirmation of the current state appends nothing.
     */
    fun append(record: ConsentRecord)
}
