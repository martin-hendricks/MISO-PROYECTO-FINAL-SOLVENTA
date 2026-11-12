package com.grupo8_uniandes.solventa.ui.shell

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ProfilingConsent
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ProfilingConsentRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ProfilingConsentUi(
    val consent: ProfilingConsent? = null,
    val sheetOpen: Boolean = false,
    val revoking: Boolean = false,
    val failed: Boolean = false,
) {
    val visible: Boolean
        get() = consent is ProfilingConsent.Granted || consent is ProfilingConsent.Revoked
}

class ProfilingConsentViewModel(
    private val repository: ProfilingConsentRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(ProfilingConsentUi())
    val state: StateFlow<ProfilingConsentUi> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            val answer = repository.read()
            _state.update { it.copy(consent = (answer as? StandInAnswer.Ready)?.value) }
        }
    }

    fun open() {
        if (_state.value.consent !is ProfilingConsent.Granted) return
        _state.update { it.copy(sheetOpen = true, failed = false) }
    }

    fun close() {
        _state.update { it.copy(sheetOpen = false) }
    }

    fun revoke() {
        if (_state.value.revoking) return
        _state.update { it.copy(revoking = true) }
        viewModelScope.launch {
            val answer = repository.revoke()
            _state.update {
                if (answer is StandInAnswer.Ready) {
                    it.copy(consent = answer.value, sheetOpen = false, revoking = false)
                } else {
                    it.copy(sheetOpen = false, revoking = false, failed = true)
                }
            }
        }
    }
}
