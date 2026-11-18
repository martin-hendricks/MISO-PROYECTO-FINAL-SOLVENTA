package com.grupo8_uniandes.solventa.prestadores

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.assistance.ClaimProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.FindProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCenter
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderPage
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderQuery
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

enum class ProviderMapPhase {
    Loading,
    NearMe,
    ChooseCity,
    ClaimMode,
    Empty,
    Error,
}

enum class ProviderPlacement {
    Unknown,
    Near,
    City,
    Claim,
}

data class MapaPrestadoresUi(
    val phase: ProviderMapPhase = ProviderMapPhase.Loading,
    val placement: ProviderPlacement = ProviderPlacement.Unknown,
    val providers: List<Provider> = emptyList(),
    val centro: ProviderCenter? = null,
    val radioKm: Double = 10.0,
    val ramo: String? = null,
    val ramoFijo: String? = null,
    val ciudad: String? = null,
    val numero: String? = null,
    val sinGeoetiqueta: Boolean = false,
    val mapsKey: String = "",
)

class MapaPrestadoresViewModel(
    private val find: FindProviders,
    private val locator: DeviceLocator,
    private val mapsKey: String,
    private val claimId: String? = null,
) : ViewModel() {
    private val _state = MutableStateFlow(MapaPrestadoresUi(mapsKey = mapsKey))
    val state: StateFlow<MapaPrestadoresUi> = _state.asStateFlow()
    private var job: Job? = null
    private var lat: Double? = null
    private var lng: Double? = null

    fun onLocationPermission(granted: Boolean) {
        if (!claimId.isNullOrBlank()) {
            loadClaim()
            return
        }
        if (!granted) {
            job?.cancel()
            lat = null
            lng = null
            _state.value = cityShell()
            return
        }
        job?.cancel()
        job = viewModelScope.launch {
            _state.value = _state.value.copy(phase = ProviderMapPhase.Loading)
            val point = withTimeoutOrNull(LOCATION_WAIT_MS) { locator.current() }
            if (point == null) {
                lat = null
                lng = null
                _state.value = cityShell()
                return@launch
            }
            lat = point.lat
            lng = point.lng
            publishNear()
        }
    }

    fun selectCity(ciudad: String) {
        val ramo = _state.value.ramoFijo ?: _state.value.ramo
        job?.cancel()
        job = viewModelScope.launch {
            _state.value = _state.value.copy(ciudad = ciudad, phase = ProviderMapPhase.Loading)
            when (val answer = find.search(ProviderQuery(ciudad = ciudad, ramo = ramo, radioKm = 10.0))) {
                is StandInAnswer.Ready -> {
                    val claim = !claimId.isNullOrBlank()
                    _state.value = _state.value.copy(
                        phase = if (claim) ProviderMapPhase.ClaimMode else ProviderMapPhase.ChooseCity,
                        placement = if (claim) ProviderPlacement.Claim else ProviderPlacement.City,
                        providers = answer.value.prestadores,
                        centro = answer.value.centro,
                        radioKm = answer.value.radioKm,
                        ciudad = ciudad,
                        mapsKey = mapsKey,
                    )
                }
                else -> _state.value = failed()
            }
        }
    }

    fun selectRamo(ramo: String?) {
        val fijo = _state.value.ramoFijo
        if (fijo != null && ramo != fijo) return
        _state.value = _state.value.copy(ramo = ramo)
        when {
            lat != null && lng != null && claimId.isNullOrBlank() -> {
                job?.cancel()
                job = viewModelScope.launch {
                    _state.value = _state.value.copy(phase = ProviderMapPhase.Loading)
                    publishNear()
                }
            }
            !_state.value.ciudad.isNullOrBlank() -> selectCity(_state.value.ciudad!!)
        }
    }

    fun retry() {
        when {
            !claimId.isNullOrBlank() && _state.value.ciudad.isNullOrBlank() -> loadClaim()
            !_state.value.ciudad.isNullOrBlank() && lat == null -> selectCity(_state.value.ciudad!!)
            lat != null && lng != null -> {
                job?.cancel()
                job = viewModelScope.launch {
                    _state.value = _state.value.copy(phase = ProviderMapPhase.Loading)
                    publishNear()
                }
            }
        }
    }

    private fun loadClaim() {
        val id = claimId ?: return
        job?.cancel()
        job = viewModelScope.launch {
            _state.value = _state.value.copy(phase = ProviderMapPhase.Loading)
            when (val answer = find.nearClaim(id)) {
                is StandInAnswer.Ready -> _state.value = claimState(answer.value)
                else -> _state.value = failed()
            }
        }
    }

    private suspend fun publishNear() {
        val hereLat = lat ?: return
        val hereLng = lng ?: return
        when (
            val answer = find.search(
                ProviderQuery(
                    lat = hereLat,
                    lng = hereLng,
                    ramo = _state.value.ramo,
                    radioKm = 10.0,
                ),
            )
        ) {
            is StandInAnswer.Ready -> _state.value = nearState(answer.value)
            else -> _state.value = failed()
        }
    }

    private fun nearState(page: ProviderPage) = MapaPrestadoresUi(
        phase = if (page.prestadores.isEmpty()) ProviderMapPhase.Empty else ProviderMapPhase.NearMe,
        placement = ProviderPlacement.Near,
        providers = page.prestadores,
        centro = page.centro,
        radioKm = page.radioKm,
        ramo = _state.value.ramo,
        mapsKey = mapsKey,
    )

    private fun claimState(page: ClaimProviders): MapaPrestadoresUi {
        val emptyNear = page.prestadores.isEmpty() && !page.sinGeoetiqueta
        return MapaPrestadoresUi(
            phase = if (emptyNear) ProviderMapPhase.Empty else ProviderMapPhase.ClaimMode,
            placement = ProviderPlacement.Claim,
            providers = page.prestadores,
            centro = page.centro,
            radioKm = page.radioKm,
            ramo = page.ramoFijo,
            ramoFijo = page.ramoFijo,
            numero = page.numero,
            sinGeoetiqueta = page.sinGeoetiqueta,
            mapsKey = mapsKey,
        )
    }

    private fun cityShell() = MapaPrestadoresUi(
        phase = ProviderMapPhase.ChooseCity,
        placement = ProviderPlacement.City,
        ramo = _state.value.ramo,
        mapsKey = mapsKey,
    )

    private companion object {
        const val LOCATION_WAIT_MS = 4_000L
    }

    private fun failed() = _state.value.copy(
        phase = ProviderMapPhase.Error,
        providers = emptyList(),
        mapsKey = mapsKey,
    )
}
