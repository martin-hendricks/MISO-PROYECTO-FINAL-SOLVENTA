package com.grupo8_uniandes.solventa.domain.consent

enum class ConsentState {
    NotGranted,
    Granted,
    Revoked,
}

enum class ConsentAction {
    Grant,
    Revoke,
}

data class ConsentRecord(
    val action: ConsentAction,
    val atMillis: Long,
    val resulting: ConsentState,
)

data class ConsentSnapshot(
    val state: ConsentState = ConsentState.NotGranted,
    val records: List<ConsentRecord> = emptyList(),
)
