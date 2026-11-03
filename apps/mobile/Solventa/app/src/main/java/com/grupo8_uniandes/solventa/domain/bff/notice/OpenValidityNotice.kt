package com.grupo8_uniandes.solventa.domain.bff.notice

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.push.PushDestination
import com.grupo8_uniandes.solventa.domain.bff.push.PushNotice

enum class ValidityKind {
    EXPIRY,
    RENEWAL,
}

data class ValidityReading(
    val kind: ValidityKind,
    val banner: String,
    val poliza: String,
)

class OpenValidityNotice(
    private val notices: NoticeRepository,
) {
    suspend fun openExpiry(): ValidityReading? = reading(ValidityKind.EXPIRY)

    suspend fun openRenewal(): ValidityReading? = reading(ValidityKind.RENEWAL)

    suspend fun open(push: PushNotice): ValidityReading? = when {
        push.poliza != POLICY -> null
        push.destino == PushDestination.AVISO_VENCIMIENTO -> openExpiry()
        push.destino == PushDestination.AVISO_RENOVACION -> openRenewal()
        else -> null
    }

    private suspend fun reading(kind: ValidityKind): ValidityReading? {
        val listed = notices.list() as? StandInAnswer.Ready ?: return null
        val match = listed.value.any { it.matches(kind) }
        if (!match) return null
        return when (kind) {
            ValidityKind.EXPIRY -> ValidityReading(kind, EXPIRY_BANNER, POLICY)
            ValidityKind.RENEWAL -> ValidityReading(kind, RENEWAL_BANNER, POLICY)
        }
    }

    private fun ValidityNotice.matches(kind: ValidityKind): Boolean = when (kind) {
        ValidityKind.EXPIRY -> tipo == EXPIRY && poliza == POLICY
        ValidityKind.RENEWAL -> tipo == RENEWAL && poliza == POLICY && estado == IN_FORCE
    }

    companion object {
        const val POLICY = "POL-88219-CO"
        const val EXPIRY = "vencimiento"
        const val RENEWAL = "renovacion"
        const val IN_FORCE = "vigente"
        const val EXPIRY_BANNER =
            "Paso del ciclo: tu póliza de Protección de dispositivo vence en 7 días. La renovación la confirma un operador."
        const val RENEWAL_BANNER =
            "Renovación confirmada · Protección de dispositivo vigente hasta 12 mar 2028. La ejecuta un operador; aquí solo la consultas."
    }
}
