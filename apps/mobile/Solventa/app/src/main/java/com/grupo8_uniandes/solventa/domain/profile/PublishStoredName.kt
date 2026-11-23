package com.grupo8_uniandes.solventa.domain.profile

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository

data class AccountName(val nombre: String, val apellidos: String)

interface AccountNameRepository {
    suspend fun read(): StandInAnswer<AccountName>

    suspend fun save(nombre: String, apellidos: String): StandInAnswer<AccountName>
}

class IdleAccountNameRepository : AccountNameRepository {
    override suspend fun read() = StandInAnswer.Ready(AccountName("", ""))

    override suspend fun save(nombre: String, apellidos: String) =
        StandInAnswer.Ready(AccountName(nombre, apellidos))
}

/**
 * The phone keeps the name from registration. An account created before that
 * name reached the server still has empty columns, and the CMS edit form
 * copies those columns. Fill them once, and leave a name the operator already set.
 */
class PublishStoredName(
    private val registration: RegistrationRepository,
    private val names: AccountNameRepository,
) {
    suspend operator fun invoke() {
        val nombre = registration.storedGivenName()
        val apellidos = registration.storedSurnames()
        if (nombre.isEmpty() && apellidos.isEmpty()) return
        val current = names.read()
        if (current !is StandInAnswer.Ready) return
        if (current.value.nombre.isNotBlank() || current.value.apellidos.isNotBlank()) return
        names.save(nombre, apellidos)
    }
}
