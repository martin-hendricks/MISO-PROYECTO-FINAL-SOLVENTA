package com.grupo8_uniandes.solventa.offer

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.ShowFirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.formatOfferDate
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
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
)

class OfferViewModel(
    private val showFirmOffer: ShowFirmOffer,
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

    private fun FirmOffer.toUi(region: Region): OfferUiState {
        val inForce = estado == IN_FORCE
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
        const val EXPIRED = "oferta_vencida"
    }
}
