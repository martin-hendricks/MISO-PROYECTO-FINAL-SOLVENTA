package com.grupo8_uniandes.solventa.domain.issuance

/**
 * Local check for the confirmation screen. The values never leave the phone.
 */
object CardConfirmation {
    fun valid(
        titular: String,
        numero: String,
        mes: String,
        anio: String,
        codigo: String,
    ): Boolean {
        if (titular.isBlank()) return false
        val digits = numero.filter { it.isDigit() }
        if (digits.length != CardNumber.limit(digits)) return false
        if (!CardExpiry.complete(mes, anio)) return false
        val code = codigo.trim()
        return code.length in 3..4 && code.all { it.isDigit() }
    }
}
