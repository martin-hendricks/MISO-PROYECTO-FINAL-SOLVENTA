package com.grupo8_uniandes.solventa.claim

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimDetail
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class DetailPhase { Pending, Ready, Failed, Missing }

data class DetailUi(
    val phase: DetailPhase = DetailPhase.Pending,
    val claim: ClaimDetail? = null,
)

class SiniestroDetalleViewModel(
    private val claims: ClaimRepository,
    private val claimId: String,
) : ViewModel() {
    private val _state = MutableStateFlow(DetailUi())
    val state: StateFlow<DetailUi> = _state.asStateFlow()

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            _state.value = DetailUi(phase = DetailPhase.Pending)
            _state.value = when (val answer = claims.detail(claimId)) {
                is StandInAnswer.Ready -> DetailUi(DetailPhase.Ready, answer.value)
                is StandInAnswer.Rejected -> DetailUi(phase = DetailPhase.Missing)
                else -> DetailUi(phase = DetailPhase.Failed)
            }
        }
    }
}
