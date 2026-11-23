package com.grupo8_uniandes.solventa.domain.registration

object PasswordLength {
    const val MIN = 8
    const val MAX = 72

    fun meetsMinimum(raw: String): Boolean = raw.trim().length >= MIN

    fun meetsMaximum(raw: String): Boolean {
        val length = raw.trim().length
        return length in 1..MAX
    }

    fun accepted(raw: String): Boolean = meetsMinimum(raw) && meetsMaximum(raw)
}
