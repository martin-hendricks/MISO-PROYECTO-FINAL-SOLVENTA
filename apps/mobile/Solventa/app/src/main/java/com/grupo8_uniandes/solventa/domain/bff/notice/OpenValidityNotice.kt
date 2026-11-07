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
    val poliza: String,
    val venceEn: String?,
)

class OpenValidityNotice(
    private val notices: NoticeRepository,
) {
    suspend fun openExpiry(): ValidityReading? = reading(ValidityKind.EXPIRY)

    suspend fun openRenewal(): ValidityReading? = reading(ValidityKind.RENEWAL)

    // El push solo trae el número de póliza y el tipo de aviso -- no sabe si
    // ese aviso sigue vigente en la lista real, así que busca la lectura
    // real correspondiente a esa póliza en vez de confiar en el cuerpo del
    // push. Si esa póliza ya no tiene un aviso activo (venció el push, o el
    // backend ya lo resolvió), no abre nada.
    suspend fun open(push: PushNotice): ValidityReading? = when (push.destino) {
        PushDestination.AVISO_VENCIMIENTO -> openExpiry()?.takeIf { it.poliza == push.poliza }
        PushDestination.AVISO_RENOVACION -> openRenewal()?.takeIf { it.poliza == push.poliza }
        else -> null
    }

    private suspend fun reading(kind: ValidityKind): ValidityReading? {
        val listed = notices.list() as? StandInAnswer.Ready ?: return null
        val match = listed.value.firstOrNull { it.matches(kind) } ?: return null
        return ValidityReading(kind, match.poliza, match.venceEn)
    }

    private fun ValidityNotice.matches(kind: ValidityKind): Boolean = when (kind) {
        ValidityKind.EXPIRY -> tipo == EXPIRY
        ValidityKind.RENEWAL -> tipo == RENEWAL && estado == IN_FORCE
    }

    companion object {
        const val EXPIRY = "vencimiento"
        const val RENEWAL = "renovacion"
        const val IN_FORCE = "vigente"

        // Ya no filtra el matching (reading() acepta cualquier póliza real),
        // pero sigue siendo el número de muestra que usan los fixtures/tests
        // de navegación (CustomerNavHostTest.kt, PublishedSamples) -- se
        // conserva con el mismo nombre para no tocar ese archivo, fuera del
        // alcance de este cambio.
        const val POLICY = "POL-88219-CO"
    }
}
