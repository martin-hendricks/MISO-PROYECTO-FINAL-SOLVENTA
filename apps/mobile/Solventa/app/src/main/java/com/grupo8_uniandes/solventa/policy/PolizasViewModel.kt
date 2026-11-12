package com.grupo8_uniandes.solventa.policy

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
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
    val requested: String = "",
    val detail: PolicyDetail? = null,
    val notice: Boolean = false,
    val claims: List<ClaimSummary> = emptyList(),
) {
    val numero: String get() = detail?.numero ?: requested
    val queHacer: String get() = detail?.queHacer.orEmpty()
}

class PolizaDetalleViewModel(
    issuance: IssuanceRepository,
    private val numero: String,
    memory: PolicyMemory = InMemoryPolicyStore(),
    private val claims: ClaimRepository? = null,
) : ViewModel() {
    private val consult = ConsultPolicies(issuance, memory)
    private val _state = MutableStateFlow(PolicyDetailUiState(requested = numero))
    val state: StateFlow<PolicyDetailUiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _state.value = PolicyDetailUiState(phase = PolicyPhase.Pending, requested = numero)
            val result = consult.open(numero)
            val related = claimsFor(numero)
            _state.value = when {
                result.detail != null -> PolicyDetailUiState(
                    phase = PolicyPhase.Ready,
                    requested = numero,
                    detail = result.detail,
                    notice = result.notice,
                    claims = related,
                )
                result.missing -> PolicyDetailUiState(phase = PolicyPhase.Failed, requested = numero)
                else -> PolicyDetailUiState(phase = PolicyPhase.Pending, requested = numero)
            }
        }
    }

    private suspend fun claimsFor(numero: String): List<ClaimSummary> {
        val answer = claims?.list() ?: return emptyList()
        return if (answer is StandInAnswer.Ready) {
            answer.value.filter { it.poliza == numero }
        } else {
            emptyList()
        }
    }
}
