package com.grupo8_uniandes.solventa.offer

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.ShowFirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.formatOfferDate
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import java.math.BigDecimal

enum class OfferPhase { Pending, Failed, Ready }

data class OfferUiState(
    val phase: OfferPhase = OfferPhase.Pending,
    val premiumText: String = "",
    val endDateText: String = "",
    val acceptEnabled: Boolean = false,
    val expired: Boolean = false,
    val cotizacionId: String = "",
    val ramo: String = "",
    val accepting: Boolean = false,
    val acceptFailed: Boolean = false,
    val acceptedId: String? = null,
)

class OfferViewModel(
    private val showFirmOffer: ShowFirmOffer,
    private val offers: OfferRepository,
    private val cotizacionId: String,
    private val region: Region = Region.Colombia,
) : ViewModel() {
    private val _state = MutableStateFlow(OfferUiState(cotizacionId = cotizacionId))
    val state: StateFlow<OfferUiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _state.value = OfferUiState(phase = OfferPhase.Pending, cotizacionId = cotizacionId)
            _state.value = when (val answer = showFirmOffer.load(cotizacionId)) {
            StandInAnswer.Pending -> OfferUiState(phase = OfferPhase.Pending, cotizacionId = cotizacionId)
            StandInAnswer.Failed -> OfferUiState(phase = OfferPhase.Failed, cotizacionId = cotizacionId)
            is StandInAnswer.Ready -> answer.value.toUi(region)
            }
        }
    }

    fun accept() {
        val current = _state.value
        if (current.accepting || current.acceptedId != null || !current.acceptEnabled) return
        viewModelScope.launch {
            _state.update { it.copy(accepting = true, acceptFailed = false) }
            _state.update { state ->
                when (val answer = offers.accept(cotizacionId)) {
                    is StandInAnswer.Ready -> state.copy(
                        accepting = false,
                        acceptFailed = false,
                        acceptedId = answer.value.cotizacionId,
                    )
                    else -> state.copy(accepting = false, acceptFailed = true)
                }
            }
        }
    }

    fun consumeAccepted() {
        _state.update { it.copy(acceptedId = null) }
    }

    private fun FirmOffer.toUi(region: Region): OfferUiState {
        val inForce = estado == IN_FORCE || estado == QUOTED
        val expired = estado == EXPIRED
        return OfferUiState(
            phase = OfferPhase.Ready,
            premiumText = formatPremium(BigDecimal(prima), moneda, region),
            endDateText = formatOfferDate(venceEn, region),
            acceptEnabled = inForce,
            expired = expired,
            cotizacionId = cotizacionId,
            ramo = ramo,
        )
    }

    private companion object {
        const val IN_FORCE = "oferta_vigente"
        const val QUOTED = "cotizada"
        const val EXPIRED = "oferta_vencida"
    }
}
