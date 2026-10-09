package com.grupo8_uniandes.solventa.registration

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.registration.KeyDocumentNumber
import com.grupo8_uniandes.solventa.data.registration.KeyDocumentType
import com.grupo8_uniandes.solventa.data.registration.KeyEmail
import com.grupo8_uniandes.solventa.data.registration.KeyGivenName
import com.grupo8_uniandes.solventa.data.registration.KeyPassword
import com.grupo8_uniandes.solventa.data.registration.KeyRegistrationCompleted
import com.grupo8_uniandes.solventa.data.registration.KeySurnames
import com.grupo8_uniandes.solventa.data.registration.RegistrationPrefsFile
import com.grupo8_uniandes.solventa.data.registration.SharedPrefsRegistrationRepository
import com.grupo8_uniandes.solventa.domain.registration.Registration
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import java.io.File

@RunWith(RobolectricTestRunner::class)
class SharedPrefsRegistrationRepositoryTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val repository = SharedPrefsRegistrationRepository(context)

    @Before
    fun clearStore() {
        context.getSharedPreferences(RegistrationPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
        File(context.filesDir, "registration/document.jpg").delete()
    }

    @Test
    fun givenNoSave_whenRead_thenNotCompleted() {
        assertNull(repository.read())
        assertFalse(
            context.getSharedPreferences(RegistrationPrefsFile, Context.MODE_PRIVATE)
                .getBoolean(KeyRegistrationCompleted, false),
        )
    }

    @Test
    fun givenSave_whenRead_thenTextsAndPhotoMatch() {
        val first = registration(byteArrayOf(1, 2, 3))
        repository.save(first)

        val stored = repository.read()
        assertEquals("Camila", stored?.givenName)
        assertEquals("Restrepo", stored?.surnames)
        assertEquals("camila@correo.com", stored?.email)
        assertEquals("CC", stored?.documentType)
        assertEquals("1023456789", stored?.documentNumber)
        assertEquals("secret", stored?.password)
        assertTrue(byteArrayOf(1, 2, 3).contentEquals(stored?.documentPhoto))
        val prefs = context.getSharedPreferences(RegistrationPrefsFile, Context.MODE_PRIVATE)
        assertEquals("Camila", prefs.getString(KeyGivenName, null))
        assertEquals("Restrepo", prefs.getString(KeySurnames, null))
        assertEquals("camila@correo.com", prefs.getString(KeyEmail, null))
        assertEquals("CC", prefs.getString(KeyDocumentType, null))
        assertEquals("1023456789", prefs.getString(KeyDocumentNumber, null))
        assertEquals("secret", prefs.getString(KeyPassword, null))
        assertTrue(prefs.getBoolean(KeyRegistrationCompleted, false))

        repository.save(registration(byteArrayOf(9, 9)))
        assertTrue(byteArrayOf(9, 9).contentEquals(repository.read()?.documentPhoto))
        assertEquals("camila@correo.com", repository.read()?.email)
    }

    private fun registration(photo: ByteArray) = Registration(
        givenName = "Camila",
        surnames = "Restrepo",
        email = "camila@correo.com",
        documentType = "CC",
        documentNumber = "1023456789",
        password = "secret",
        documentPhoto = photo,
    )
}
