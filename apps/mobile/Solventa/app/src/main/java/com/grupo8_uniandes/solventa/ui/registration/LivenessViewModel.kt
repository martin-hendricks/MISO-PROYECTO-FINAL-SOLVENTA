package com.grupo8_uniandes.solventa.ui.registration

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.domain.bff.signup.LivenessCheck
import com.grupo8_uniandes.solventa.domain.bff.signup.LivenessRepository
import com.grupo8_uniandes.solventa.domain.bff.signup.RecordStep
import com.grupo8_uniandes.solventa.domain.bff.signup.SelfieOutcome
import com.grupo8_uniandes.solventa.domain.bff.signup.VerifySelfie
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.domain.registration.documentTypes
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

sealed interface LivenessEffect {
    data object OpenHome : LivenessEffect

    data object OpenLogin : LivenessEffect

    data object RequestCamera : LivenessEffect
}

enum class LivenessPhase {
    Form,
    Camera,
    Sending,
    Passed,
    Failed,
    Denied,
    Unavailable,
}

data class LivenessUiState(
    val givenName: String = "",
    val surnames: String = "",
    val email: String = "",
    val documentType: String = "",
    val documentTypeOptions: List<String> = documentTypes(Region.Colombia),
    val documentNumber: String = "",
    val password: String = "",
    val phase: LivenessPhase = LivenessPhase.Form,
    val photo: ByteArray? = null,
    val captureTicket: Int = 0,
    val retryRecordOnly: Boolean = false,
    val effect: LivenessEffect? = null,
)

class LivenessViewModel(
    private val repository: RegistrationRepository,
    region: Region = Region.Colombia,
    private val verifySelfie: VerifySelfie = VerifySelfie(IdleLiveness()),
) : ViewModel() {
    private val documentPhoto: ByteArray = repository.read()?.documentPhoto ?: byteArrayOf()
    private val _state = MutableStateFlow(prefill(repository.read(), region))
    val state: StateFlow<LivenessUiState> = _state.asStateFlow()
    private var check: Job? = null

    fun onGivenName(value: String) = edit { it.copy(givenName = value) }

    fun onSurnames(value: String) = edit { it.copy(surnames = value) }

    fun onEmail(value: String) = edit { it.copy(email = value) }

    fun onDocumentType(value: String) = edit { it.copy(documentType = value) }

    fun onDocumentNumber(value: String) = edit { it.copy(documentNumber = value) }

    fun onPassword(value: String) = edit { it.copy(password = value) }

    fun continuar() {
        val current = _state.value
        if (documentPhoto.isNotEmpty()) {
            repository.update(
                Registration(
                    givenName = current.givenName.trim(),
                    surnames = current.surnames.trim(),
                    email = current.email.trim(),
                    documentType = current.documentType.trim(),
                    documentNumber = current.documentNumber.trim(),
                    password = current.password.trim(),
                    documentPhoto = documentPhoto.copyOf(),
                ),
            )
        }
        _state.value = current.copy(phase = LivenessPhase.Camera, effect = null)
    }

    fun onShutter(cameraGranted: Boolean) {
        if (_state.value.phase == LivenessPhase.Sending) return
        if (!cameraGranted) {
            _state.value = _state.value.copy(effect = LivenessEffect.RequestCamera)
            return
        }
        if (_state.value.phase != LivenessPhase.Camera && _state.value.phase != LivenessPhase.Failed) return
        _state.value = _state.value.copy(captureTicket = _state.value.captureTicket + 1, effect = null)
    }

    fun onCameraResult(granted: Boolean) {
        if (!granted) {
            _state.value = _state.value.copy(phase = LivenessPhase.Denied, effect = null)
            return
        }
        val current = _state.value
        _state.value = current.copy(
            phase = LivenessPhase.Camera,
            captureTicket = current.captureTicket + 1,
            effect = null,
        )
    }

    fun onCameraUnavailable() {
        _state.value = _state.value.copy(phase = LivenessPhase.Denied, photo = null, effect = null)
    }

    fun onPhoto(bytes: ByteArray) {
        val phase = _state.value.phase
        if (phase != LivenessPhase.Camera && phase != LivenessPhase.Failed) return
        if (_state.value.effect == LivenessEffect.OpenLogin) return
        send(bytes, recordOnly = false)
    }

    fun repetirFoto() {
        if (_state.value.phase == LivenessPhase.Denied) {
            _state.value = _state.value.copy(effect = LivenessEffect.RequestCamera)
            return
        }
        _state.value = _state.value.copy(phase = LivenessPhase.Camera, photo = null, effect = null)
    }

    fun reintentar() {
        val current = _state.value
        val photo = current.photo ?: return
        if (current.retryRecordOnly) {
            check?.cancel()
            _state.value = current.copy(phase = LivenessPhase.Sending, effect = null)
            check = viewModelScope.launch {
                apply(verifySelfie.retryRecord(), photo, recordOnly = true)
            }
            return
        }
        send(photo, recordOnly = false)
    }

    fun continuarCamara() {
        if (_state.value.phase != LivenessPhase.Passed) return
        finish()
    }

    fun continuarConDocumento() {
        check?.cancel()
        _state.value = _state.value.copy(photo = null, retryRecordOnly = false)
        finish()
    }

    fun back() {
        check?.cancel()
        _state.value = _state.value.copy(
            phase = LivenessPhase.Form,
            photo = null,
            retryRecordOnly = false,
            effect = null,
        )
    }

    fun yaTengoCuenta() {
        check?.cancel()
        _state.value = _state.value.copy(effect = LivenessEffect.OpenLogin)
    }

    fun dismissLogin() {
        if (_state.value.effect != LivenessEffect.OpenLogin) return
        _state.value = _state.value.copy(effect = null)
    }

    fun consumeEffect() {
        if (_state.value.effect == LivenessEffect.RequestCamera) {
            _state.value = _state.value.copy(effect = null)
        }
    }

    private fun send(bytes: ByteArray, recordOnly: Boolean) {
        check?.cancel()
        _state.value = _state.value.copy(
            phase = LivenessPhase.Sending,
            photo = bytes,
            retryRecordOnly = recordOnly,
            effect = null,
        )
        check = viewModelScope.launch {
            apply(verifySelfie(bytes), bytes, recordOnly)
        }
    }

    private fun apply(outcome: SelfieOutcome, bytes: ByteArray, recordOnly: Boolean) {
        if (_state.value.effect == LivenessEffect.OpenLogin) return
        _state.value = when (outcome) {
            SelfieOutcome.Passed -> _state.value.copy(
                phase = LivenessPhase.Passed,
                photo = bytes,
                retryRecordOnly = false,
            )
            SelfieOutcome.Failed -> _state.value.copy(
                phase = LivenessPhase.Failed,
                photo = null,
                retryRecordOnly = false,
            )
            is SelfieOutcome.Unavailable -> _state.value.copy(
                phase = LivenessPhase.Unavailable,
                photo = bytes,
                retryRecordOnly = outcome.step == RecordStep.Record || recordOnly,
            )
        }
    }

    private fun finish() {
        repository.completeLiveness()
        _state.value = _state.value.copy(photo = null, effect = LivenessEffect.OpenHome)
    }

    private fun edit(change: (LivenessUiState) -> LivenessUiState) {
        _state.value = change(_state.value).copy(effect = null)
    }
}

private class IdleLiveness : LivenessRepository {
    override suspend fun check(photo: ByteArray) = LivenessCheck.Unavailable

    override suspend fun record(result: Liveness) = StandInAnswer.Failed
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
