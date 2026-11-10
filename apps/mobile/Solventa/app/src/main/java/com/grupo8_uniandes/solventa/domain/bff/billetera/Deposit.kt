package com.grupo8_uniandes.solventa.domain.bff.billetera

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import java.math.BigDecimal

enum class DepositType { Assisted, Automatic }

data class Deposit(
    val id: String,
    val siniestroId: String,
    val tipo: DepositType,
    val ramo: String,
    val resumen: String,
    val poliza: String,
    val monto: BigDecimal,
    val moneda: String,
    val comprobante: String,
    val depositadoEn: String,
)

data class Wallet(
    val moneda: String,
    val totalRecibido: BigDecimal,
    val movimientos: List<Deposit>,
)

interface DepositRepository {
    suspend fun wallet(): StandInAnswer<Wallet>
    suspend fun deposit(id: String): StandInAnswer<Deposit>
}
