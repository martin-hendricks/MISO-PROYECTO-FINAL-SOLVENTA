package com.grupo8_uniandes.solventa.data.registration

import android.content.Context
import android.content.SharedPreferences
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import java.io.File

internal const val RegistrationPrefsFile = "registration_prefs"
internal const val KeyGivenName = "given_name"
internal const val KeySurnames = "surnames"
internal const val KeyEmail = "email"
internal const val KeyDocumentType = "document_type"
internal const val KeyDocumentNumber = "document_number"
internal const val KeyPassword = "password"
internal const val KeyRegistrationCompleted = "registration_completed"

class SharedPrefsRegistrationRepository(
    private val prefs: SharedPreferences,
    private val filesDir: File,
) : RegistrationRepository {
    constructor(context: Context) : this(
        context.applicationContext.getSharedPreferences(
            RegistrationPrefsFile,
            Context.MODE_PRIVATE,
        ),
        context.applicationContext.filesDir,
    )

    override fun read(): Registration? {
        if (!prefs.getBoolean(KeyRegistrationCompleted, false)) return null
        val photo = photoFile().takeIf { it.isFile }?.readBytes() ?: return null
        return Registration(
            givenName = prefs.getString(KeyGivenName, "").orEmpty(),
            surnames = prefs.getString(KeySurnames, "").orEmpty(),
            email = prefs.getString(KeyEmail, "").orEmpty(),
            documentType = prefs.getString(KeyDocumentType, "").orEmpty(),
            documentNumber = prefs.getString(KeyDocumentNumber, "").orEmpty(),
            password = prefs.getString(KeyPassword, "").orEmpty(),
            documentPhoto = photo,
        )
    }

    override fun save(registration: Registration) {
        val directory = File(filesDir, "registration")
        directory.mkdirs()
        File(directory, "document.jpg").writeBytes(registration.documentPhoto)
        prefs.edit()
            .putString(KeyGivenName, registration.givenName)
            .putString(KeySurnames, registration.surnames)
            .putString(KeyEmail, registration.email)
            .putString(KeyDocumentType, registration.documentType)
            .putString(KeyDocumentNumber, registration.documentNumber)
            .putString(KeyPassword, registration.password)
            .putBoolean(KeyRegistrationCompleted, true)
            .commit()
    }

    private fun photoFile(): File = File(filesDir, "registration/document.jpg")
}
