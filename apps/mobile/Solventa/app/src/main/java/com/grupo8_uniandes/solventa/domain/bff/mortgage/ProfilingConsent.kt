package com.grupo8_uniandes.solventa.domain.bff.mortgage

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

sealed interface ProfilingConsent {
    data class Granted(val grantedAt: String) : ProfilingConsent

    data class Revoked(val revokedAt: String) : ProfilingConsent

    data object None : ProfilingConsent
}

interface ProfilingConsentRepository {
    suspend fun read(): StandInAnswer<ProfilingConsent>

    suspend fun revoke(): StandInAnswer<ProfilingConsent>
}
