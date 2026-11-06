package com.grupo8_uniandes.solventa.issuance

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.issuance.CardConfirmation
import com.grupo8_uniandes.solventa.domain.issuance.CardExpiry
import com.grupo8_uniandes.solventa.domain.issuance.CardNumber
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

data class CardUiState(
    val titular: String = "",
    val numero: String = "",
    val mes: String = "",
    val anio: String = "",
    val codigo: String = "",
) {
    val canConfirm: Boolean
        get() = CardConfirmation.valid(titular, numero, mes, anio, codigo)
}

class ConfirmacionTarjetaViewModel : ViewModel() {
    private val _state = MutableStateFlow(CardUiState())
    val state: StateFlow<CardUiState> = _state.asStateFlow()
    private var started = false

    fun onTitular(value: String) = edit { it.copy(titular = value) }

    fun onNumero(value: String) = edit { it.copy(numero = CardNumber.digits(value)) }

    fun onMes(value: String) = edit { it.copy(mes = CardExpiry.month(value)) }

    fun onAnio(value: String) = edit { it.copy(anio = CardExpiry.year(value)) }

    fun onCodigo(value: String) = edit { it.copy(codigo = value) }

    fun confirm(): Boolean {
        if (started || !_state.value.canConfirm) return false
        started = true
        _state.value = CardUiState()
        return true
    }

    fun discard() {
        if (started) return
        _state.value = CardUiState()
    }

    private fun edit(change: (CardUiState) -> CardUiState) {
        if (started) return
        _state.update(change)
    }
}
