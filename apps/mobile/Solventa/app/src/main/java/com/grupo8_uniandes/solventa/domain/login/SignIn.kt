package com.grupo8_uniandes.solventa.domain.login

import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository

open class SignIn(
    private val repository: RegistrationRepository,
) {
    open fun submit(email: String, password: String): SignInResult {
        val trimmedEmail = email.trim()
        val trimmedPassword = password.trim()
        if (trimmedEmail.isEmpty() || trimmedPassword.isEmpty()) {
            return SignInResult.Incomplete
        }
        val saved = repository.read() ?: return SignInResult.Rejected
        return if (saved.email == trimmedEmail && saved.password == trimmedPassword) {
            SignInResult.SignedIn
        } else {
            SignInResult.Rejected
        }
    }
}
