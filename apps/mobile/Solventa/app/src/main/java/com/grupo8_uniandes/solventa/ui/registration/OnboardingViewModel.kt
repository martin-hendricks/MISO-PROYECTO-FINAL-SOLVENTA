package com.grupo8_uniandes.solventa.ui.registration

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.registration.AccountDraft
import com.grupo8_uniandes.solventa.domain.registration.EmailAddress
import com.grupo8_uniandes.solventa.domain.registration.EmailStatus
import com.grupo8_uniandes.solventa.domain.registration.RegisterAccount
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

sealed interface OnboardingEffect {
    data object ContinueToHome : OnboardingEffect

    data object OpenLogin : OnboardingEffect
}

data class OnboardingUiState(
    val givenName: String = "",
    val surnames: String = "",
    val email: String = "",
    val documentType: String = "",
    val documentNumber: String = "",
    val password: String = "",
    val hasPhoto: Boolean = false,
    val emailError: Boolean = false,
    val continuarEnabled: Boolean = false,
    val effect: OnboardingEffect? = null,
)

class OnboardingViewModel(
    private val registerAccount: RegisterAccount,
) : ViewModel() {
    private var photo: ByteArray? = null
    private val _state = MutableStateFlow(OnboardingUiState())
    val state: StateFlow<OnboardingUiState> = _state.asStateFlow()

    fun onGivenName(value: String) = edit { it.copy(givenName = value) }

    fun onSurnames(value: String) = edit { it.copy(surnames = value) }

    fun onEmail(value: String) = edit { it.copy(email = value) }

    fun onDocumentType(value: String) = edit { it.copy(documentType = value) }

    fun onDocumentNumber(value: String) = edit { it.copy(documentNumber = value) }

    fun onPassword(value: String) = edit { it.copy(password = value) }

    fun attachPhoto(bytes: ByteArray) {
        photo = bytes.copyOf()
        edit { it }
    }

    fun photoDeclined() {
        photo = null
        edit { it }
    }

    fun continuar() {
        val current = _state.value
        if (!current.continuarEnabled) return
        val saved = registerAccount.submit(current.toDraft(photo))
        if (saved) {
            _state.value = current.copy(effect = OnboardingEffect.ContinueToHome)
        }
    }

    fun yaTengoCuenta() {
        _state.value = _state.value.copy(effect = OnboardingEffect.OpenLogin)
    }

    private fun edit(change: (OnboardingUiState) -> OnboardingUiState) {
        val next = change(_state.value).copy(effect = null)
        _state.value = present(next)
    }

    private fun present(draft: OnboardingUiState): OnboardingUiState {
        val emailStatus = EmailAddress.status(draft.email)
        val photoReady = photo?.isNotEmpty() == true
        val textsReady = listOf(
            draft.givenName,
            draft.surnames,
            draft.email,
            draft.documentType,
            draft.documentNumber,
            draft.password,
        ).all { it.trim().isNotEmpty() }
        return draft.copy(
            hasPhoto = photoReady,
            emailError = emailStatus == EmailStatus.Invalid,
            continuarEnabled = textsReady && emailStatus == EmailStatus.Valid && photoReady,
        )
    }

    private fun OnboardingUiState.toDraft(photo: ByteArray?) = AccountDraft(
        givenName = givenName,
        surnames = surnames,
        email = email,
        documentType = documentType,
        documentNumber = documentNumber,
        password = password,
        documentPhoto = photo,
    )
}
