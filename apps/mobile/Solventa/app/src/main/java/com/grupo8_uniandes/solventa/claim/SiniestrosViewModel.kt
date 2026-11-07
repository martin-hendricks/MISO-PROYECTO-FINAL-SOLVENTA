package com.grupo8_uniandes.solventa.claim

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimChip
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.ListClaims
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenParametricPayment
import com.grupo8_uniandes.solventa.domain.bff.claim.filtered
import kotlinx.coroutines.Job
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlin.coroutines.coroutineContext

enum class ClaimsPhase { Pending, Failed, Ready }

object ParametricTarget {
    var claimId: String = ""
}

data class ClaimsUiState(
    val phase: ClaimsPhase = ClaimsPhase.Pending,
    val claims: List<ClaimSummary> = emptyList(),
    val openedClaimId: String? = null,
    val chip: ClaimChip = ClaimChip.Todos,
    val openParametric: Boolean = false,
) {
    val visible: List<ClaimSummary> get() = claims.filtered(chip)
}

class SiniestrosViewModel(
    claims: ClaimRepository,
) : ViewModel() {
    private val listClaims = ListClaims(claims)
    private val _state = MutableStateFlow(ClaimsUiState())
    val state: StateFlow<ClaimsUiState> = _state.asStateFlow()
    private var loadJob: Job? = null

    init {
        refresh()
    }

    fun refresh() {
        if (loadJob?.isActive == true) return
        loadJob = viewModelScope.launch {
            val answer = listClaims()
            coroutineContext.ensureActive()
            _state.value = when (answer) {
                StandInAnswer.Pending -> _state.value.copy(phase = ClaimsPhase.Pending)
                StandInAnswer.Failed, is StandInAnswer.Rejected -> _state.value.copy(phase = ClaimsPhase.Failed)
                is StandInAnswer.Ready -> ClaimsUiState(
                    phase = ClaimsPhase.Ready,
                    claims = answer.value,
                    chip = _state.value.chip,
                )
            }
        }
    }

    fun selectChip(chip: ClaimChip) {
        _state.value = _state.value.copy(chip = chip)
    }

    fun openClaim(id: String) {
        val claim = _state.value.claims.find { it.siniestroId == id }
        val parametric = id == OpenParametricPayment.STORED_ID ||
            (claim?.tipo == "parametrico" && claim.estado == ClaimStatus.PAGADO)
        ParametricTarget.claimId = if (parametric && id != OpenParametricPayment.STORED_ID) id else ""
        _state.value = _state.value.copy(openedClaimId = id, openParametric = parametric)
    }

    fun consumeOpenedClaim() {
        _state.value = _state.value.copy(openedClaimId = null)
    }
}
