package com.grupo8_uniandes.solventa.issuance

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class EmisionPhase { Processing, Issued, Rejected }

data class EmisionUiState(
    val phase: EmisionPhase = EmisionPhase.Processing,
    val cotizacionId: String? = null,
)

class EmisionViewModel(
    private val offers: OfferRepository,
    private val cotizacionId: String,
) : ViewModel() {
    private val _state = MutableStateFlow(EmisionUiState())
    val state: StateFlow<EmisionUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            _state.value = when (val answer = offers.accept(cotizacionId)) {
                is StandInAnswer.Ready -> EmisionUiState(EmisionPhase.Issued, answer.value.cotizacionId)
                else -> EmisionUiState(EmisionPhase.Rejected)
            }
        }
    }
}
