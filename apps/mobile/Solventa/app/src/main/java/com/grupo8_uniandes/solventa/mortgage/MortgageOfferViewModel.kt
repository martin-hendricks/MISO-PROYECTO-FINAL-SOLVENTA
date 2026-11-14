package com.grupo8_uniandes.solventa.mortgage

import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageCredit
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.mortgage.CreditProfile
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageQuote
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface MortgageOfferUi {
    data object Consent : MortgageOfferUi

    data object Requesting : MortgageOfferUi

    data class Offer(val quote: MortgageQuote) : MortgageOfferUi

    data object Unavailable : MortgageOfferUi
}

class MortgageOfferViewModel(
    private val mortgage: MortgageRepository,
) : ViewModel() {
    private val _state = MutableStateFlow<MortgageOfferUi>(MortgageOfferUi.Consent)
    val state: StateFlow<MortgageOfferUi> = _state.asStateFlow()

    fun authorize(credit: MortgageCredit? = null) {
        val current = _state.value
        if (current != MortgageOfferUi.Consent && current != MortgageOfferUi.Unavailable) return
        _state.value = MortgageOfferUi.Requesting
        viewModelScope.launch {
            val profile = credit?.let { CreditProfile(it.valor, it.plazoMeses, consentimientoPerfil = true) } ?: AUTHORIZED
            _state.value = when (val answer = mortgage.offer(profile)) {
                is StandInAnswer.Ready -> MortgageOfferUi.Offer(answer.value)
                else -> MortgageOfferUi.Unavailable
            }
        }
    }

    private companion object {
        val AUTHORIZED = CreditProfile(valor = 0, plazoMeses = 0, consentimientoPerfil = true)
    }
}
