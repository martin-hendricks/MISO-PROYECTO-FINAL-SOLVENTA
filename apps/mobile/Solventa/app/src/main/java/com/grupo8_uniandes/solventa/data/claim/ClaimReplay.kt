package com.grupo8_uniandes.solventa.data.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.EvidenceBytes

class ClaimReplay(
    private val store: EncryptedNoticeStore,
    private val claims: ClaimRepository,
) {
    suspend fun replay(): ClaimReceipt? {
        val kept = store.read() ?: return null
        if (kept.files.size != kept.notice.adjuntos.size || kept.files.any { it.isEmpty() }) return null
        kept.notice.adjuntos.zip(kept.files).forEach { (file, bytes) ->
            EvidenceBytes.keep(file.nombre, bytes)
        }
        return when (val answer = claims.notify(kept.notice, kept.key)) {
            is StandInAnswer.Ready -> {
                store.clear()
                answer.value
            }
            else -> null
        }
    }
}
