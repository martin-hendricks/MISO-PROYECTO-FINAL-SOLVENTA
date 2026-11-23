package com.grupo8_uniandes.solventa.domain.profile

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class PublishStoredNameTest {
    @Test
    fun givenABlankServerName_whenThePhoneHasOne_thenItIsSaved() = runBlocking {
        val names = RecordingNames(AccountName("", ""))
        PublishStoredName(stored("john", "doe"), names).invoke()
        assertEquals(AccountName("john", "doe"), names.saved)
    }

    @Test
    fun givenANameAlreadyOnTheServer_whenPublished_thenItStays() = runBlocking {
        val names = RecordingNames(AccountName("Camila", "Restrepo"))
        PublishStoredName(stored("john", "doe"), names).invoke()
        assertNull(names.saved)
    }

    @Test
    fun givenNoLocalName_whenPublished_thenTheServerIsLeftAlone() = runBlocking {
        val names = RecordingNames(AccountName("", ""))
        PublishStoredName(stored("  ", ""), names).invoke()
        assertNull(names.saved)
    }

    private fun stored(nombre: String, apellidos: String) = object : RegistrationRepository {
        override fun read() = Registration(nombre, apellidos, "john@doe.com", "CC", "1", "x", byteArrayOf())
        override fun save(registration: Registration) = Unit
    }

    private class RecordingNames(private val current: AccountName) : AccountNameRepository {
        var saved: AccountName? = null

        override suspend fun read() = StandInAnswer.Ready(current)

        override suspend fun save(nombre: String, apellidos: String): StandInAnswer<AccountName> {
            saved = AccountName(nombre, apellidos)
            return StandInAnswer.Ready(saved!!)
        }
    }
}
