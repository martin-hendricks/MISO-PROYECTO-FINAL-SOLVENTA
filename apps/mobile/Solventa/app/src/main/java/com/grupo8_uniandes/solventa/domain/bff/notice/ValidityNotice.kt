package com.grupo8_uniandes.solventa.domain.bff.notice

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

data class ValidityNotice(
    val tipo: String,
    val poliza: String,
    val venceEn: String?,
    val estado: String?,
)

interface NoticeRepository {
    fun list(): StandInAnswer<List<ValidityNotice>>
}
