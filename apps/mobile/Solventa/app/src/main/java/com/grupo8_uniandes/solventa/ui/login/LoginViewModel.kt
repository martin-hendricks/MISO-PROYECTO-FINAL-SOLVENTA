package com.grupo8_uniandes.solventa.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.login.DeviceUnlock
import com.grupo8_uniandes.solventa.domain.login.OpenHomeFromDeviceUnlock
import com.grupo8_uniandes.solventa.domain.login.SignIn
import com.grupo8_uniandes.solventa.domain.login.SignInResult
import com.grupo8_uniandes.solventa.domain.registration.BiometricLogin
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class LoginFailure {
    None,
    Rejected,
    Unavailable,
}

sealed interface LoginEffect {
    data object OpenHome : LoginEffect

    data object ConfirmBiometric : LoginEffect
}

data class LoginUiState(
    val email: String = "",
    val password: String = "",
    val failure: LoginFailure = LoginFailure.None,
    val biometricFallback: Boolean = false,
    val effect: LoginEffect? = null,
)

fun interface BiometricGate {
    fun enabled(): Boolean
}

fun interface EnableBiometric {
    fun enable()
}

fun interface RemoteSessionOpener {
    suspend fun open(email: String, password: String): Boolean
}

fun interface StoredBiometricLogin {
    fun read(): BiometricLogin?
}

fun interface RememberBiometricLogin {
    fun remember(email: String, password: String)
}

class LoginViewModel(
    private val signIn: SignIn,
    private val openHomeFromDeviceUnlock: OpenHomeFromDeviceUnlock = OpenHomeFromDeviceUnlock(),
    private val biometricEnabled: BiometricGate = BiometricGate { true },
    private val enableBiometric: EnableBiometric = EnableBiometric { },
    private val openRemoteSession: RemoteSessionOpener? = null,
    private val storedBiometricLogin: StoredBiometricLogin = StoredBiometricLogin { null },
    private val rememberBiometricLogin: RememberBiometricLogin = RememberBiometricLogin { _, _ -> },
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
        if (submitting || current.effect != null) return
        attempt(current.email, current.password, fromBiometric = false)
    }

    private fun homeEffect(): LoginEffect = if (biometricEnabled.enabled()) {
        LoginEffect.OpenHome
    } else {
        LoginEffect.ConfirmBiometric
    }

    fun onDeviceUnlock(result: DeviceUnlock) {
        val current = _state.value
        if (submitting || current.effect != null) return
        if (!openHomeFromDeviceUnlock(result)) {
            _state.value = current.copy(biometricFallback = true)
            return
        }
        val stored = storedBiometricLogin.read()
        if (stored == null) {
            _state.value = current.copy(biometricFallback = true)
            return
        }
        attempt(stored.email, stored.password, fromBiometric = true)
    }

    private fun attempt(email: String, password: String, fromBiometric: Boolean) {
        val current = _state.value
        submitting = true
        val result = signIn.submit(email, password)
        val openRemoteSession = openRemoteSession
        if (result == SignInResult.SignedIn && openRemoteSession != null) {
            viewModelScope.launch {
                val opened = try {
                    openRemoteSession.open(email, password)
                } catch (_: Exception) {
                    false
                }
                submitting = false
                _state.value = if (opened) {
                    signedIn(current, email, password, fromBiometric)
                } else {
                    failed(current, LoginFailure.Unavailable, fromBiometric)
                }
            }
            return
        }
        submitting = false
        _state.value = when (result) {
            SignInResult.SignedIn -> signedIn(current, email, password, fromBiometric)
            SignInResult.Rejected -> failed(current, LoginFailure.Rejected, fromBiometric)
            SignInResult.Incomplete -> if (fromBiometric) {
                current.copy(biometricFallback = true)
            } else {
                current.copy(failure = LoginFailure.None, effect = null)
            }
            SignInResult.Unavailable -> failed(current, LoginFailure.Unavailable, fromBiometric)
        }
    }

    private fun signedIn(
        current: LoginUiState,
        email: String,
        password: String,
        fromBiometric: Boolean,
    ): LoginUiState {
        rememberBiometricLogin.remember(email, password)
        return current.copy(
            email = "",
            password = "",
            failure = LoginFailure.None,
            effect = if (fromBiometric) LoginEffect.OpenHome else homeEffect(),
        )
    }

    private fun failed(
        current: LoginUiState,
        failure: LoginFailure,
        fromBiometric: Boolean,
    ): LoginUiState = current.copy(
        failure = failure,
        effect = null,
        biometricFallback = current.biometricFallback || fromBiometric,
    )

    fun acceptBiometric() {
        val current = _state.value
        if (current.effect != LoginEffect.ConfirmBiometric) return
        enableBiometric.enable()
        _state.value = current.copy(effect = LoginEffect.OpenHome)
    }

    fun declineBiometric() {
        val current = _state.value
        if (current.effect != LoginEffect.ConfirmBiometric) return
        _state.value = current.copy(effect = LoginEffect.OpenHome)
    }

    fun consumeEffect() {
        if (_state.value.effect == null) return
        _state.value = _state.value.copy(effect = null)
    }
}
