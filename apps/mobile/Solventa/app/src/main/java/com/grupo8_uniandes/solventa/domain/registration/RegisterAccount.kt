package com.grupo8_uniandes.solventa.domain.registration

class AccountDraft(
    val givenName: String,
    val surnames: String,
    val email: String,
    val documentType: String,
    val documentNumber: String,
    val password: String,
    val documentPhoto: ByteArray?,
)

open class RegisterAccount(
    private val repository: RegistrationRepository,
) {
    open fun submit(draft: AccountDraft): Boolean {
        val givenName = draft.givenName.trim()
        val surnames = draft.surnames.trim()
        val email = draft.email.trim()
        val documentType = draft.documentType.trim()
        val documentNumber = draft.documentNumber.trim()
        val password = draft.password.trim()
        val photo = draft.documentPhoto
        if (
            givenName.isEmpty() ||
            surnames.isEmpty() ||
            email.isEmpty() ||
            documentType.isEmpty() ||
            documentNumber.isEmpty() ||
            password.isEmpty() ||
            photo == null ||
            photo.isEmpty() ||
            EmailAddress.status(email) != EmailStatus.Valid
        ) {
            return false
        }
        repository.save(
            Registration(
                givenName = givenName,
                surnames = surnames,
                email = email,
                documentType = documentType,
                documentNumber = documentNumber,
                password = password,
                documentPhoto = photo.copyOf(),
            ),
        )
        return true
    }
}
