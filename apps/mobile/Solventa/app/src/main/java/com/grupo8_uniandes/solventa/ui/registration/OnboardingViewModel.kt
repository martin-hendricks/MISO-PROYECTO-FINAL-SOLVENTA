package com.grupo8_uniandes.solventa.ui.registration

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.region.Region
import kotlinx.coroutines.launch
import com.grupo8_uniandes.solventa.domain.registration.AccountDraft
import com.grupo8_uniandes.solventa.domain.registration.EmailAddress
import com.grupo8_uniandes.solventa.domain.registration.EmailStatus
import com.grupo8_uniandes.solventa.domain.registration.RegisterAccount
import com.grupo8_uniandes.solventa.domain.registration.documentTypes
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

sealed interface OnboardingEffect {
    data object ContinueToLiveness : OnboardingEffect

    data object OpenLogin : OnboardingEffect
}

data class OnboardingUiState(
    val givenName: String = "",
    val surnames: String = "",
    val email: String = "",
    val documentType: String = "",
    val documentTypeOptions: List<String> = documentTypes(Region.Colombia),
    val documentNumber: String = "",
    val password: String = "",
    val passwordConfirm: String = "",
    val hasPhoto: Boolean = false,
    val emailError: Boolean = false,
    val continuarEnabled: Boolean = false,
    val awaitingPhoto: Boolean = false,
    val unavailable: Boolean = false,
    val effect: OnboardingEffect? = null,
)

class OnboardingViewModel(
    private val registerAccount: RegisterAccount,
    private val region: Region = Region.Colombia,
    private val openRemoteSession: (suspend (String, String) -> Boolean)? = null,
) : ViewModel() {
    private var photo: ByteArray? = null
    private var submitting = false
    private val _state = MutableStateFlow(
        OnboardingUiState(documentTypeOptions = documentTypes(region)),
    )
    val state: StateFlow<OnboardingUiState> = _state.asStateFlow()

    fun onGivenName(value: String) = edit { it.copy(givenName = value) }

    fun onSurnames(value: String) = edit { it.copy(surnames = value) }

    fun onEmail(value: String) = edit { it.copy(email = value) }

    fun onDocumentType(value: String) = edit { it.copy(documentType = value) }

    fun onDocumentNumber(value: String) = edit { it.copy(documentNumber = value) }

    fun onPassword(value: String) = edit { it.copy(password = value) }

    fun onPasswordConfirm(value: String) = edit { it.copy(passwordConfirm = value) }

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
        if (!current.continuarEnabled || submitting) return
        val saved = registerAccount.submit(current.toDraft(photo), region)
        if (!saved) return
        val opener = openRemoteSession
        if (opener == null) {
            _state.value = current.copy(unavailable = false, effect = OnboardingEffect.ContinueToLiveness)
            return
        }
        submitting = true
        viewModelScope.launch {
            val opened = try {
                opener(current.email.trim(), current.password.trim())
            } catch (_: Exception) {
                false
            }
            submitting = false
            _state.value = if (opened) {
                current.copy(unavailable = false, effect = OnboardingEffect.ContinueToLiveness)
            } else {
                current.copy(unavailable = true, effect = null)
            }
        }
    }

    fun yaTengoCuenta() {
        _state.value = _state.value.copy(effect = OnboardingEffect.OpenLogin)
    }

    fun dismissLogin() {
        if (_state.value.effect != OnboardingEffect.OpenLogin) return
        _state.value = _state.value.copy(effect = null)
    }

    private fun edit(change: (OnboardingUiState) -> OnboardingUiState) {
        val next = change(_state.value).copy(effect = null, unavailable = false)
        _state.value = present(next)
    }

    private fun present(draft: OnboardingUiState): OnboardingUiState {
        val emailStatus = EmailAddress.status(draft.email)
        val photoReady = photo?.isNotEmpty() == true
        val passwordText = draft.password.trim()
        val confirmText = draft.passwordConfirm.trim()
        val textsReady = listOf(
            draft.givenName,
            draft.surnames,
            draft.email,
            draft.documentNumber,
        ).all { it.trim().isNotEmpty() }
        val passwordReady = passwordText.isNotEmpty() && passwordText == confirmText
        val typeReady = draft.documentType.trim() in documentTypes(region)
        val detailsReady = textsReady &&
            passwordReady &&
            typeReady &&
            emailStatus == EmailStatus.Valid
        return draft.copy(
            hasPhoto = photoReady,
            emailError = emailStatus == EmailStatus.Invalid,
            continuarEnabled = detailsReady && photoReady,
            awaitingPhoto = detailsReady && !photoReady,
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
