package com.grupo8_uniandes.solventa.claim

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.LocalRenewal
import com.grupo8_uniandes.solventa.domain.bff.claim.MemoryRenewal
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenParametricPayment
import com.grupo8_uniandes.solventa.domain.bff.claim.ParametricNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ParametricReceipt
import com.grupo8_uniandes.solventa.domain.bff.push.NoticeEntry
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ParametricUiState(
    val notice: ParametricNotice? = null,
    val receipt: ParametricReceipt? = null,
    val poliza: String? = null,
    val renewalChecked: Boolean = false,
    val loading: Boolean = false,
    val failed: Boolean = false,
    val missing: Boolean = false,
)

class ParametricoViewModel(
    private val payments: OpenParametricPayment,
    private val claims: ClaimRepository? = null,
    private val renewal: LocalRenewal = MemoryRenewal(),
) : ViewModel() {
    private val _state = MutableStateFlow(ParametricUiState())
    val state: StateFlow<ParametricUiState> = _state.asStateFlow()

    fun load(claimId: String = OpenParametricPayment.STORED_ID) {
        viewModelScope.launch {
            val notice = payments.open(claimId)
            _state.value = _state.value.copy(
                notice = notice,
                poliza = OpenParametricPayment.POLICY,
                renewalChecked = renewal.read(OpenParametricPayment.POLICY),
                failed = notice == null,
                loading = false,
            )
        }
    }

    fun loadStored(claimId: String) {
        val repo = claims ?: return
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, failed = false, missing = false)
            _state.value = when (val answer = repo.detail(claimId)) {
                is StandInAnswer.Ready -> {
                    val notice = answer.value.storedPayment()
                    val poliza = answer.value.poliza
                    ParametricUiState(
                        notice = notice,
                        poliza = poliza,
                        renewalChecked = poliza?.let(renewal::read) ?: false,
                        failed = notice == null,
                    )
                }
                is StandInAnswer.Rejected -> ParametricUiState(missing = true)
                else -> ParametricUiState(failed = true)
            }
        }
    }

    fun setRenewal(enabled: Boolean) {
        val poliza = _state.value.poliza ?: return
        renewal.write(poliza, enabled)
        _state.value = _state.value.copy(renewalChecked = enabled)
    }

    fun openPush(push: NoticeEntry) {
        val notice = payments.open(push) ?: return
        _state.value = _state.value.copy(notice = notice)
    }

    fun offerReceipt(): ParametricReceipt? {
        val notice = _state.value.notice ?: return null
        val receipt = payments.receipt(notice)
        _state.value = _state.value.copy(receipt = receipt)
        return receipt
    }
}
