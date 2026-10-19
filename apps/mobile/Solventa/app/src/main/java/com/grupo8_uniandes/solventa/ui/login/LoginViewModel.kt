package com.grupo8_uniandes.solventa.ui.login

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.login.SignIn
import com.grupo8_uniandes.solventa.domain.login.SignInResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

enum class LoginFailure {
    None,
    Rejected,
    Unavailable,
}

sealed interface LoginEffect {
    data object OpenHome : LoginEffect
}

data class LoginUiState(
    val email: String = "",
    val password: String = "",
    val failure: LoginFailure = LoginFailure.None,
    val effect: LoginEffect? = null,
)

class LoginViewModel(
    private val signIn: SignIn,
) : ViewModel() {
    private val _state = MutableStateFlow(LoginUiState())
    val state: StateFlow<LoginUiState> = _state.asStateFlow()
    private var submitting = false

    fun onEmail(value: String) {
        if (submitting || _state.value.effect != null) return
        _state.value = _state.value.copy(email = value)
    }

    fun onPassword(value: String) {
        if (submitting || _state.value.effect != null) return
        _state.value = _state.value.copy(password = value)
    }

    fun ingresar() {
        val current = _state.value
        if (submitting || current.effect == LoginEffect.OpenHome) return
        submitting = true
        val result = signIn.submit(current.email, current.password)
        submitting = false
        _state.value = when (result) {
            SignInResult.SignedIn -> current.copy(
                failure = LoginFailure.None,
                effect = LoginEffect.OpenHome,
            )
            SignInResult.Rejected -> current.copy(
                failure = LoginFailure.Rejected,
                effect = null,
            )
            SignInResult.Incomplete -> current.copy(
                failure = LoginFailure.None,
                effect = null,
            )
            SignInResult.Unavailable -> current.copy(
                failure = LoginFailure.Unavailable,
                effect = null,
            )
        }
    }
}
