package com.grupo8_uniandes.solventa.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.AcceptedQuote
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.domain.home.LoadInicio
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.coroutines.coroutineContext

data class HomeUiState(
    val panel: HomePanel = HomePanel(),
    val failed: Boolean = false,
    val accepting: Boolean = false,
    val acceptedId: String? = null,
)

class HomeViewModel(
    private val loadInicio: LoadInicio,
    private val offers: OfferRepository = RejectingOffers,
    private val reloadDispatcher: CoroutineDispatcher = Dispatchers.IO,
) : ViewModel() {
    private val _state = MutableStateFlow(read())
    val state: StateFlow<HomeUiState> = _state.asStateFlow()
    private var loadJob: Job? = null

    fun refresh() {
        if (loadJob?.isActive == true) return
        loadJob = viewModelScope.launch {
            val panel = withContext(reloadDispatcher) { loadInicio.panel() }
            coroutineContext.ensureActive()
            _state.update { current ->
                if (panel == null) {
                    current.copy(failed = true)
                } else {
                    current.copy(panel = panel, failed = false)
                }
            }
        }
    }

    fun accept(cotizacionId: String) {
        if (_state.value.accepting || _state.value.acceptedId != null) return
        viewModelScope.launch {
            _state.update { it.copy(accepting = true) }
            _state.update { state ->
                when (offers.accept(cotizacionId)) {
                    is StandInAnswer.Ready -> state.copy(
                        accepting = false,
                        failed = false,
                        acceptedId = cotizacionId,
                    )
                    else -> state.copy(accepting = false, failed = true, acceptedId = null)
                }
            }
        }
    }

    fun consumeAccepted() {
        _state.update { it.copy(acceptedId = null) }
    }

    private fun read(): HomeUiState {
        val panel = loadInicio.panel()
        return if (panel == null) HomeUiState(failed = true) else HomeUiState(panel = panel)
    }
}

private object RejectingOffers : OfferRepository {
    override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> = StandInAnswer.Failed

    override suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer> = StandInAnswer.Failed

    override suspend fun accept(cotizacionId: String): StandInAnswer<AcceptedQuote> = StandInAnswer.Failed
}
