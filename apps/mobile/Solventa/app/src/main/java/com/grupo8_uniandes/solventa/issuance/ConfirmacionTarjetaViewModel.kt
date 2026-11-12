package com.grupo8_uniandes.solventa.issuance

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.ShowFirmOffer
import com.grupo8_uniandes.solventa.domain.issuance.CardConfirmation
import com.grupo8_uniandes.solventa.domain.issuance.CardExpiry
import com.grupo8_uniandes.solventa.domain.issuance.CardNumber
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.math.BigDecimal

data class CardUiState(
    val titular: String = "",
    val numero: String = "",
    val mes: String = "",
    val anio: String = "",
    val codigo: String = "",
    val premiumText: String = "",
) {
    val canConfirm: Boolean
        get() = CardConfirmation.valid(titular, numero, mes, anio, codigo)
}

class ConfirmacionTarjetaViewModel(
    prima: Long = 0,
    moneda: String = "COP",
    private val offerId: String = "",
    private val offers: ShowFirmOffer? = null,
    private val region: Region = Region.Colombia,
) : ViewModel() {
    private val _state = MutableStateFlow(CardUiState(premiumText = premiumLine(prima, moneda, region)))
    val state: StateFlow<CardUiState> = _state.asStateFlow()
    private var started = false

    init {
        if (prima == 0L && offerId.isNotBlank() && offers != null) {
            viewModelScope.launch {
                val answer = offers.load(offerId)
                if (answer is StandInAnswer.Ready) {
                    val text = premiumLine(answer.value.prima, answer.value.moneda, region)
                    if (text.isNotEmpty()) _state.update { it.copy(premiumText = text) }
                }
            }
        }
    }

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

internal fun premiumLine(amount: Long, moneda: String, region: Region): String {
    if (amount <= 0L) return ""
    return formatPremium(BigDecimal(amount), moneda.ifBlank { "COP" }, region)
}
