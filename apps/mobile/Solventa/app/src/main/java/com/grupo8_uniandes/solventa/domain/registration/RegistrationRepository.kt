package com.grupo8_uniandes.solventa.domain.registration

interface RegistrationRepository {
    /** Null while registration is not completed. */
    fun read(): Registration?

    /** Stores the six trimmed texts and the photo, and marks registration completed. */
    fun save(registration: Registration)

    fun biometricUnlockEnabled(): Boolean = false

    /** True when the customer has not turned huella o rostro off. A missing choice still offers it. */
    fun biometricPromptOffered(): Boolean = !prefsChoiceExists() || biometricUnlockEnabled()

    fun prefsChoiceExists(): Boolean = false

    fun setBiometricUnlock(enabled: Boolean) = Unit

    fun enableBiometricUnlock() = setBiometricUnlock(true)

    fun livenessCompleted(): Boolean = false

    fun completeLiveness() = Unit

    /** Email and password biometrics uses to sign in after the device check. */
    fun biometricLogin(): BiometricLogin? = null

    fun rememberBiometricLogin(email: String, password: String) = Unit

    /** Rewrites the saved account without changing the biometric choice or the liveness flag. */
    fun update(registration: Registration) = Unit
}
