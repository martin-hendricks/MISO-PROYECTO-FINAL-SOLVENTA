package com.grupo8_uniandes.solventa.policy

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.issuance.ConsultPolicies
import com.grupo8_uniandes.solventa.domain.bff.issuance.InMemoryPolicyStore
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyMemory
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
    val notice: Boolean = false,
)

class PolizasViewModel(
    issuance: IssuanceRepository,
    memory: PolicyMemory = InMemoryPolicyStore(),
) : ViewModel() {
    private val consult = ConsultPolicies(issuance, memory)
    private val _state = MutableStateFlow(WalletUiState())
    val state: StateFlow<WalletUiState> = _state.asStateFlow()
    private var loadJob: Job? = null

    init {
        refresh()
    }

    fun refresh() {
        if (loadJob?.isActive == true) return
        loadJob = viewModelScope.launch {
            val result = consult.list()
            coroutineContext.ensureActive()
            _state.value = when {
                result.policies.isEmpty() && !result.empty -> WalletUiState(phase = WalletPhase.Pending)
                result.policies.isEmpty() -> WalletUiState(phase = WalletPhase.Failed, notice = result.notice)
                else -> WalletUiState(phase = WalletPhase.Ready, policies = result.policies, notice = result.notice)
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
    val notice: Boolean = false,
)

class PolizaDetalleViewModel(
    issuance: IssuanceRepository,
    private val numero: String,
    memory: PolicyMemory = InMemoryPolicyStore(),
) : ViewModel() {
    private val consult = ConsultPolicies(issuance, memory)
    private val _state = MutableStateFlow(PolicyDetailUiState(numero = numero))
    val state: StateFlow<PolicyDetailUiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _state.value = PolicyDetailUiState(phase = PolicyPhase.Pending, numero = numero)
            val result = consult.open(numero)
            _state.value = when {
                result.detail != null -> result.detail.toUi().copy(notice = result.notice)
                result.missing -> PolicyDetailUiState(phase = PolicyPhase.Failed, numero = numero)
                else -> PolicyDetailUiState(phase = PolicyPhase.Pending, numero = numero)
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
