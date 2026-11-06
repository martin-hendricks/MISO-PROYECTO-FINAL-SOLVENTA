package com.grupo8_uniandes.solventa.policy

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.issuance.AcceptOffer
import com.grupo8_uniandes.solventa.domain.bff.issuance.AcceptOutcome
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

internal fun AcceptOutcome.toIssuanceUi(): IssuanceUi = when (this) {
    is AcceptOutcome.Issued -> IssuanceUi.Issued(policy.numero, policy.ramo)
    is AcceptOutcome.Refused -> IssuanceUi.Refused(rejection.motivo)
    AcceptOutcome.Ignored, AcceptOutcome.Waiting, AcceptOutcome.Unavailable -> IssuanceUi.Waiting
}

sealed interface IssuanceUi {
    data object Waiting : IssuanceUi

    data class Issued(val numero: String, val ramo: String) : IssuanceUi

    data class Refused(val motivo: String) : IssuanceUi
}

class IssuanceViewModel(
    private val acceptOffer: AcceptOffer,
    private val offerId: String,
) : ViewModel() {
    private val _state = MutableStateFlow<IssuanceUi>(IssuanceUi.Waiting)
    val state: StateFlow<IssuanceUi> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            _state.value = acceptOffer.accept(offerId).toIssuanceUi()
        }
    }
}
