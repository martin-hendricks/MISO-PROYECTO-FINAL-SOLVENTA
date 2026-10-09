package com.grupo8_uniandes.solventa.domain.registration

/**
 * A finished account. An unfinished draft is not a registration.
 * Text is stored trimmed. The photo is one JPEG and is not decoded into fields.
 */
class Registration(
    val givenName: String,
    val surnames: String,
    val email: String,
    val documentType: String,
    val documentNumber: String,
    val password: String,
    val documentPhoto: ByteArray,
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is Registration) return false
        return givenName == other.givenName &&
            surnames == other.surnames &&
            email == other.email &&
            documentType == other.documentType &&
            documentNumber == other.documentNumber &&
            password == other.password &&
            documentPhoto.contentEquals(other.documentPhoto)
    }

    override fun hashCode(): Int {
        var result = givenName.hashCode()
        result = 31 * result + surnames.hashCode()
        result = 31 * result + email.hashCode()
        result = 31 * result + documentType.hashCode()
        result = 31 * result + documentNumber.hashCode()
        result = 31 * result + password.hashCode()
        result = 31 * result + documentPhoto.contentHashCode()
        return result
    }
}
