package com.grupo8_uniandes.solventa.ui.consent

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.domain.consent.ConsentSnapshot
import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

enum class ConsentSurface {
    Alta,
    Profile,
}

sealed interface ConsentEffect {
    data object OpenHome : ConsentEffect

    data object OpenAccount : ConsentEffect

    data object ReturnToHub : ConsentEffect
}

data class ConsentUiState(
    val stored: ConsentState,
    val switchOn: Boolean,
    val confirmEnabled: Boolean,
    val effect: ConsentEffect?,
)

class ConsentViewModel(
    private val change: ChangeDataTreatment,
    initial: ConsentSnapshot,
    private val surface: ConsentSurface,
) : ViewModel() {
    private val _state = MutableStateFlow(
        present(
            stored = initial.state,
            switchOn = initialSwitch(initial.state),
            effect = null,
        ),
    )
    val state: StateFlow<ConsentUiState> = _state.asStateFlow()

    fun onSwitch(on: Boolean) {
        if (_state.value.effect != null) return
        _state.value = present(_state.value.stored, on, effect = null)
    }

    fun confirm() {
        val current = _state.value
        if (!current.confirmEnabled || current.effect != null) return
        if (current.switchOn) change.grant() else change.revoke()
        val resulting = if (current.switchOn) ConsentState.Granted else ConsentState.Revoked
        val effect = if (surface == ConsentSurface.Alta) {
            ConsentEffect.OpenHome
        } else {
            ConsentEffect.ReturnToHub
        }
        _state.value = present(resulting, current.switchOn, effect)
    }

    fun back() {
        if (_state.value.effect != null) return
        _state.value = _state.value.copy(effect = ConsentEffect.OpenAccount)
    }

    fun close() {
        val stored = _state.value.stored
        _state.value = present(stored, initialSwitch(stored), effect = null)
    }

    private fun initialSwitch(stored: ConsentState): Boolean = when (surface) {
        ConsentSurface.Alta -> false
        ConsentSurface.Profile -> stored == ConsentState.Granted
    }

    private fun present(
        stored: ConsentState,
        switchOn: Boolean,
        effect: ConsentEffect?,
    ): ConsentUiState {
        val confirmEnabled = effect == null && when (surface) {
            ConsentSurface.Alta -> switchOn
            ConsentSurface.Profile -> switchOn != (stored == ConsentState.Granted)
        }
        return ConsentUiState(
            stored = stored,
            switchOn = switchOn,
            confirmEnabled = confirmEnabled,
            effect = effect,
        )
    }
}
