package com.grupo8_uniandes.solventa.domain.registration

enum class EmailStatus {
    /** Empty or only spaces. Not an error sentence. */
    Missing,

    /** Non-empty and not a single @ with a dotted domain. */
    Invalid,

    Valid,
}

object EmailAddress {
    fun status(raw: String): EmailStatus {
        val value = raw.trim()
        if (value.isEmpty()) return EmailStatus.Missing
        val parts = value.split('@')
        if (parts.size != 2) return EmailStatus.Invalid
        val local = parts[0]
        val domain = parts[1]
        if (local.isEmpty()) return EmailStatus.Invalid
        val dot = domain.indexOf('.')
        if (dot <= 0 || dot == domain.lastIndex) return EmailStatus.Invalid
        return EmailStatus.Valid
    }
}
