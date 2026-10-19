package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.domain.registration.Registration
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RegistrationTest {
    @Test
    fun givenSameFields_whenCompared_thenEqualAndSameHash() {
        val photo = byteArrayOf(1, 2)
        val left = registration(photo)
        val right = registration(photo.copyOf())

        assertTrue(left == left)
        assertTrue(left == right)
        assertEquals(left.hashCode(), right.hashCode())
        assertFalse(left.equals("Camila"))
    }

    @Test
    fun givenOneFieldDiffers_whenCompared_thenNotEqual() {
        val base = registration(byteArrayOf(1))
        val variants = listOf(
            registration(byteArrayOf(1), givenName = "Ana"),
            registration(byteArrayOf(1), surnames = "Gómez"),
            registration(byteArrayOf(1), email = "ana@correo.com"),
            registration(byteArrayOf(1), documentType = "CE"),
            registration(byteArrayOf(1), documentNumber = "9"),
            registration(byteArrayOf(1), password = "other"),
            registration(byteArrayOf(2)),
        )
        variants.forEach { other ->
            assertNotEquals(base, other)
            assertNotEquals(base.hashCode(), other.hashCode())
        }
    }

    private fun registration(
        photo: ByteArray,
        givenName: String = "Camila",
        surnames: String = "Restrepo",
        email: String = "camila@correo.com",
        documentType: String = "CC",
        documentNumber: String = "1023456789",
        password: String = "secret",
    ) = Registration(
        givenName = givenName,
        surnames = surnames,
        email = email,
        documentType = documentType,
        documentNumber = documentNumber,
        password = password,
        documentPhoto = photo,
    )
}
