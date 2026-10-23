package com.grupo8_uniandes.solventa.quote

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteAttempt
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteField
import com.grupo8_uniandes.solventa.domain.bff.offer.RequestFirmOffer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

data class QuoteUiState(
    val value: String = "",
    val brand: String = "",
    val olderThan12Months: Boolean? = null,
    val gap: QuoteField? = null,
    val pending: Boolean = false,
    val failed: Boolean = false,
    val readyId: String? = null,
    val contextId: String = "",
)

class QuoteViewModel(
    private val request: RequestFirmOffer,
    contextId: String = "",
) : ViewModel() {
    private val _state = MutableStateFlow(QuoteUiState(contextId = contextId))
    val state: StateFlow<QuoteUiState> = _state.asStateFlow()

    fun onValue(value: String) {
        _state.update { it.copy(value = value, gap = null, failed = false) }
    }

    fun onBrand(brand: String) {
        _state.update { it.copy(brand = brand, gap = null, failed = false) }
    }

    fun onAge(olderThan12Months: Boolean) {
        _state.update { it.copy(olderThan12Months = olderThan12Months, gap = null, failed = false) }
    }

    fun cotizar() {
        when (val attempt = request.submit(_state.value.value, _state.value.brand, _state.value.olderThan12Months)) {
            is QuoteAttempt.Gap -> _state.update {
                it.copy(gap = attempt.field, pending = false, failed = false, readyId = null)
            }
            is QuoteAttempt.Answer -> when (val answer = attempt.answer) {
                StandInAnswer.Pending -> _state.update {
                    it.copy(pending = true, failed = false, gap = null, readyId = null)
                }
                StandInAnswer.Failed -> _state.update {
                    it.copy(pending = false, failed = true, gap = null, readyId = null)
                }
                is StandInAnswer.Ready -> _state.update {
                    it.copy(pending = false, failed = false, gap = null, readyId = answer.value.cotizacionId)
                }
            }
        }
    }

    fun consumeReady() {
        _state.update { it.copy(readyId = null) }
    }

    fun cancel() {
        val kept = _state.value.contextId
        _state.value = QuoteUiState(contextId = kept)
    }
}
