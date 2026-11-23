package com.grupo8_uniandes.solventa.data.registration

import android.content.Context
import android.content.SharedPreferences
import com.grupo8_uniandes.solventa.domain.registration.BiometricLogin
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
internal const val KeyBiometricUnlock = "biometric_unlock"
internal const val KeyBiometricEmail = "biometric_email"
internal const val KeyBiometricPassword = "biometric_password"
internal const val KeyLivenessCompleted = "liveness_completed"

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

    override fun storedGivenName(): String = prefs.getString(KeyGivenName, "").orEmpty().trim()

    override fun storedSurnames(): String = prefs.getString(KeySurnames, "").orEmpty().trim()

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

    override fun biometricUnlockEnabled(): Boolean = prefs.getBoolean(KeyBiometricUnlock, false)

    override fun prefsChoiceExists(): Boolean = prefs.contains(KeyBiometricUnlock)

    override fun biometricPromptOffered(): Boolean =
        !prefs.contains(KeyBiometricUnlock) || prefs.getBoolean(KeyBiometricUnlock, false)

    override fun setBiometricUnlock(enabled: Boolean) {
        val editor = prefs.edit().putBoolean(KeyBiometricUnlock, enabled)
        if (!enabled) {
            editor.remove(KeyBiometricEmail).remove(KeyBiometricPassword)
        }
        editor.commit()
    }

    override fun enableBiometricUnlock() = setBiometricUnlock(true)

    override fun livenessCompleted(): Boolean = prefs.getBoolean(KeyLivenessCompleted, false)

    override fun completeLiveness() {
        prefs.edit().putBoolean(KeyLivenessCompleted, true).commit()
    }

    override fun biometricLogin(): BiometricLogin? = loginPair(
        prefs.getString(KeyBiometricEmail, null),
        prefs.getString(KeyBiometricPassword, null),
    )

    override fun rememberBiometricLogin(email: String, password: String) {
        val pair = loginPair(email, password) ?: return
        prefs.edit()
            .putString(KeyBiometricEmail, pair.email)
            .putString(KeyBiometricPassword, pair.password)
            .commit()
    }

    override fun update(registration: Registration) {
        writeAccount(registration)
    }

    override fun save(registration: Registration) {
        writeAccount(registration)
    }

    private fun writeAccount(registration: Registration) {
        val directory = File(filesDir, "registration")
        directory.mkdirs()
        File(directory, "document.jpg").writeBytes(registration.documentPhoto)
        val editor = prefs.edit()
            .putString(KeyGivenName, registration.givenName)
            .putString(KeySurnames, registration.surnames)
            .putString(KeyEmail, registration.email)
            .putString(KeyDocumentType, registration.documentType)
            .putString(KeyDocumentNumber, registration.documentNumber)
            .putString(KeyPassword, registration.password)
            .putBoolean(KeyRegistrationCompleted, true)
        editor.commit()
    }

    private fun photoFile(): File = File(filesDir, "registration/document.jpg")

    private fun loginPair(email: String?, password: String?): BiometricLogin? {
        val trimmedEmail = email?.trim().orEmpty()
        val storedPassword = password.orEmpty()
        if (trimmedEmail.isEmpty() || storedPassword.isEmpty()) return null
        return BiometricLogin(trimmedEmail, storedPassword)
    }
}
