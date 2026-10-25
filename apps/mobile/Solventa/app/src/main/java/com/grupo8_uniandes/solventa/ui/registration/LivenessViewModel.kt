package com.grupo8_uniandes.solventa.ui.registration

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.domain.registration.documentTypes
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

sealed interface LivenessEffect {
    data object OpenConsent : LivenessEffect

    data object OpenLogin : LivenessEffect
}

data class LivenessUiState(
    val givenName: String = "",
    val surnames: String = "",
    val email: String = "",
    val documentType: String = "",
    val documentTypeOptions: List<String> = documentTypes(Region.Colombia),
    val documentNumber: String = "",
    val password: String = "",
    val effect: LivenessEffect? = null,
)

class LivenessViewModel(
    private val repository: RegistrationRepository,
    region: Region = Region.Colombia,
) : ViewModel() {
    private val photo: ByteArray = repository.read()?.documentPhoto ?: byteArrayOf()
    private val _state = MutableStateFlow(prefill(repository.read(), region))
    val state: StateFlow<LivenessUiState> = _state.asStateFlow()

    fun onGivenName(value: String) = edit { it.copy(givenName = value) }

    fun onSurnames(value: String) = edit { it.copy(surnames = value) }

    fun onEmail(value: String) = edit { it.copy(email = value) }

    fun onDocumentType(value: String) = edit { it.copy(documentType = value) }

    fun onDocumentNumber(value: String) = edit { it.copy(documentNumber = value) }

    fun onPassword(value: String) = edit { it.copy(password = value) }

    fun continuar() {
        val current = _state.value
        if (photo.isNotEmpty()) {
            repository.update(
                Registration(
                    givenName = current.givenName.trim(),
                    surnames = current.surnames.trim(),
                    email = current.email.trim(),
                    documentType = current.documentType.trim(),
                    documentNumber = current.documentNumber.trim(),
                    password = current.password.trim(),
                    documentPhoto = photo.copyOf(),
                ),
            )
        }
        repository.completeLiveness()
        _state.value = current.copy(effect = LivenessEffect.OpenConsent)
    }

    fun yaTengoCuenta() {
        _state.value = _state.value.copy(effect = LivenessEffect.OpenLogin)
    }

    fun dismissLogin() {
        if (_state.value.effect != LivenessEffect.OpenLogin) return
        _state.value = _state.value.copy(effect = null)
    }

    private fun edit(change: (LivenessUiState) -> LivenessUiState) {
        _state.value = change(_state.value).copy(effect = null)
    }
}

private fun prefill(saved: Registration?, region: Region): LivenessUiState {
    val account = saved ?: return LivenessUiState(documentTypeOptions = documentTypes(region))
    return LivenessUiState(
        givenName = account.givenName,
        surnames = account.surnames,
        email = account.email,
        documentType = account.documentType,
        documentTypeOptions = documentTypes(region),
        documentNumber = account.documentNumber,
        password = account.password,
    )
}
