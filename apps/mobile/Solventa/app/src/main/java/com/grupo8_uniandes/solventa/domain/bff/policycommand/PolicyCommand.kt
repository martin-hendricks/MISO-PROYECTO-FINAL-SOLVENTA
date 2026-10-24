package com.grupo8_uniandes.solventa.domain.bff.policycommand

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuedPolicy

interface PolicyCommandRepository {
    suspend fun renew(numero: String): StandInAnswer<IssuedPolicy>

    suspend fun modify(numero: String): StandInAnswer<IssuedPolicy>

    suspend fun cancel(numero: String, motivo: String?): StandInAnswer<IssuedPolicy>
}
