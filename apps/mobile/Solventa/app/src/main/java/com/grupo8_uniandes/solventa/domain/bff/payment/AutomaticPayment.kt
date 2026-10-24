package com.grupo8_uniandes.solventa.domain.bff.payment

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

data class AutomaticPayment(
    val siniestroId: String,
    val poliza: String,
    val umbral: String,
    val monto: Long,
    val moneda: String,
    val estado: String,
)

interface PaymentRepository {
    suspend fun read(): StandInAnswer<AutomaticPayment>
}
