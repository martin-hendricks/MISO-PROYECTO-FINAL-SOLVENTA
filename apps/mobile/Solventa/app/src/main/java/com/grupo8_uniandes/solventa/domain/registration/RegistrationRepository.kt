package com.grupo8_uniandes.solventa.domain.registration

interface RegistrationRepository {
    /** Null while registration is not completed. */
    fun read(): Registration?

    /** Stores the six trimmed texts and the photo, and marks registration completed. */
    fun save(registration: Registration)
}
