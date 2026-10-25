package com.grupo8_uniandes.solventa.policy

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import kotlinx.coroutines.Job
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlin.coroutines.coroutineContext

enum class WalletPhase { Pending, Failed, Ready }

data class WalletUiState(
    val phase: WalletPhase = WalletPhase.Pending,
    val policies: List<WalletEntry> = emptyList(),
)

class PolizasViewModel(
    private val issuance: IssuanceRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(WalletUiState())
    val state: StateFlow<WalletUiState> = _state.asStateFlow()
    private var loadJob: Job? = null

    init {
        refresh()
    }

    fun refresh() {
        if (loadJob?.isActive == true) return
        loadJob = viewModelScope.launch {
            val answer = issuance.wallet()
            coroutineContext.ensureActive()
            _state.value = when (answer) {
                StandInAnswer.Pending -> _state.value.copy(phase = WalletPhase.Pending)
                StandInAnswer.Failed -> _state.value.copy(phase = WalletPhase.Failed)
                is StandInAnswer.Ready -> WalletUiState(phase = WalletPhase.Ready, policies = answer.value)
            }
        }
    }
}

enum class PolicyPhase { Pending, Failed, Ready }

data class PolicyDetailUiState(
    val phase: PolicyPhase = PolicyPhase.Pending,
    val numero: String = "",
    val ramo: String = "",
    val resumen: String = "",
    val estado: String = "",
    val venceEn: String = "",
    val queHacer: String = "",
)

class PolizaDetalleViewModel(
    private val issuance: IssuanceRepository,
    private val numero: String,
) : ViewModel() {
    private val _state = MutableStateFlow(PolicyDetailUiState(numero = numero))
    val state: StateFlow<PolicyDetailUiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _state.value = PolicyDetailUiState(phase = PolicyPhase.Pending, numero = numero)
            _state.value = when (val answer = issuance.detail(numero)) {
                StandInAnswer.Pending -> PolicyDetailUiState(phase = PolicyPhase.Pending, numero = numero)
                StandInAnswer.Failed -> PolicyDetailUiState(phase = PolicyPhase.Failed, numero = numero)
                is StandInAnswer.Ready -> answer.value.toUi()
            }
        }
    }

    private fun PolicyDetail.toUi() = PolicyDetailUiState(
        phase = PolicyPhase.Ready,
        numero = numero,
        ramo = ramo,
        resumen = resumen,
        estado = estado,
        venceEn = venceEn,
        queHacer = queHacer,
    )
}
