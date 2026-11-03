package com.grupo8_uniandes.solventa.claim

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenParametricPayment
import com.grupo8_uniandes.solventa.domain.bff.claim.ParametricNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ParametricReceipt
import com.grupo8_uniandes.solventa.domain.bff.push.PushNotice
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ParametricUiState(
    val notice: ParametricNotice? = null,
    val receipt: ParametricReceipt? = null,
)

class ParametricoViewModel(
    private val payments: OpenParametricPayment,
) : ViewModel() {
    private val _state = MutableStateFlow(ParametricUiState())
    val state: StateFlow<ParametricUiState> = _state.asStateFlow()

    fun load(claimId: String = OpenParametricPayment.STORED_ID) {
        viewModelScope.launch {
            _state.value = _state.value.copy(notice = payments.open(claimId))
        }
    }

    fun openPush(push: PushNotice) {
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
