package com.grupo8_uniandes.solventa.prestadores

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.assistance.ClaimProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.FindProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderArea
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCenter
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCity
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderPage
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderQuery
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import com.grupo8_uniandes.solventa.domain.region.RegionRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
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
    CountryEmpty,
    Error,
}

enum class ProviderPlacement {
    Unknown,
    Near,
    City,
    Claim,
}

data class CameraTarget(
    val lat: Double,
    val lng: Double,
    val zoom: Float,
    val serial: Int = 0,
)

data class MapaPrestadoresUi(
    val phase: ProviderMapPhase = ProviderMapPhase.Loading,
    val placement: ProviderPlacement = ProviderPlacement.Unknown,
    val providers: List<Provider> = emptyList(),
    val centro: ProviderCenter? = null,
    val radioKm: Double? = null,
    val ramo: String? = null,
    val ramoFijo: String? = null,
    val ciudad: String? = null,
    val numero: String? = null,
    val sinGeoetiqueta: Boolean = false,
    val mapsKey: String = "",
    val pais: String = "CO",
    val cities: List<ProviderCity> = emptyList(),
    val markedCity: String? = null,
    val area: ProviderArea? = null,
    val cameraTarget: CameraTarget? = null,
    val truncado: Boolean = false,
    val canRecenter: Boolean = false,
    val loadFailed: Boolean = false,
    val selectedIds: List<String> = emptyList(),
) {
    val selected: List<Provider>
        get() = selectedIds.mapNotNull { id -> providers.firstOrNull { it.id == id } }

    val distanceFromEvent: Boolean
        get() = placement == ProviderPlacement.Claim && !sinGeoetiqueta
}

class MapaPrestadoresViewModel(
    private val find: FindProviders,
    private val locator: DeviceLocator,
    private val regions: RegionRepository,
    private val mapsKey: String,
    private val claimId: String? = null,
) : ViewModel() {
    private val _state = MutableStateFlow(
        MapaPrestadoresUi(mapsKey = mapsKey, pais = regions.read().appliedRegion.countryCode),
    )
    val state: StateFlow<MapaPrestadoresUi> = _state.asStateFlow()
    private var job: Job? = null
    private var areaJob: Job? = null
    private var ticket = 0
    private var serial = 0
    private var claimStarted = false
    private var lat: Double? = null
    private var lng: Double? = null

    fun onLocationPermission(granted: Boolean) {
        if (!claimId.isNullOrBlank()) {
            if (!claimStarted) loadClaim()
            return
        }
        if (granted && lat != null) return
        job?.cancel()
        areaJob?.cancel()
        if (!granted) {
            lat = null
            lng = null
            job = viewModelScope.launch { startInCity() }
            return
        }
        job = viewModelScope.launch {
            update { copy(phase = ProviderMapPhase.Loading) }
            loadCities()
            val point = withTimeoutOrNull(LOCATION_WAIT_MS) { locator.current() }
            if (point == null) {
                startInCity()
                return@launch
            }
            lat = point.lat
            lng = point.lng
            update {
                copy(
                    placement = ProviderPlacement.Near,
                    canRecenter = true,
                    markedCity = null,
                    cameraTarget = target(point.lat, point.lng, NEAR_ZOOM),
                )
            }
            publishNear()
        }
    }

    fun onCameraIdle(area: ProviderArea) {
        areaJob?.cancel()
        areaJob = viewModelScope.launch {
            delay(AREA_WAIT_MS)
            loadArea(area)
        }
    }

    fun onUserPan() {
        if (_state.value.markedCity != null) update { copy(markedCity = null) }
    }

    fun recenterOnMe() {
        val hereLat = lat ?: return
        val hereLng = lng ?: return
        update { copy(markedCity = null, cameraTarget = target(hereLat, hereLng, NEAR_ZOOM)) }
    }

    fun selectCity(city: ProviderCity) {
        job?.cancel()
        job = viewModelScope.launch { showCity(city) }
    }

    fun selectRamo(ramo: String?) {
        val fijo = _state.value.ramoFijo
        if (fijo != null && ramo != fijo) return
        update { copy(ramo = ramo) }
        val area = _state.value.area
        val city = _state.value.cities.firstOrNull { it.nombre == _state.value.ciudad }
        when {
            area != null -> {
                areaJob?.cancel()
                areaJob = viewModelScope.launch { loadArea(area) }
            }
            lat != null && lng != null && claimId.isNullOrBlank() -> {
                job?.cancel()
                job = viewModelScope.launch { publishNear() }
            }
            city != null -> {
                job?.cancel()
                job = viewModelScope.launch { loadCity(city) }
            }
        }
    }

    fun selectProvider(id: String) = selectProviders(listOf(id))

    fun selectProviders(ids: List<String>) {
        update { copy(selectedIds = ids) }
    }

    fun closeCard() {
        update { copy(selectedIds = emptyList()) }
    }

    fun retry() {
        val current = _state.value
        val area = current.area
        val city = current.cities.firstOrNull { it.nombre == current.ciudad }
        when {
            current.loadFailed && area != null -> {
                areaJob?.cancel()
                areaJob = viewModelScope.launch { loadArea(area) }
            }
            !claimId.isNullOrBlank() && city == null -> loadClaim()
            lat != null && lng != null -> {
                job?.cancel()
                job = viewModelScope.launch {
                    update { copy(phase = ProviderMapPhase.Loading) }
                    publishNear()
                }
            }
            city != null -> {
                job?.cancel()
                job = viewModelScope.launch { loadCity(city) }
            }
            else -> {
                job?.cancel()
                job = viewModelScope.launch { startInCity() }
            }
        }
    }

    private suspend fun startInCity() {
        lat = null
        lng = null
        update {
            copy(
                phase = ProviderMapPhase.Loading,
                placement = ProviderPlacement.City,
                canRecenter = false,
                providers = emptyList(),
                selectedIds = emptyList(),
            )
        }
        val cities = loadCities()
        if (cities == null) {
            update { failed() }
            return
        }
        val first = cities.firstOrNull()
        if (first == null) {
            update { copy(phase = ProviderMapPhase.CountryEmpty) }
            return
        }
        showCity(first)
    }

    private suspend fun showCity(city: ProviderCity) {
        update {
            copy(
                ciudad = city.nombre,
                markedCity = city.nombre,
                cameraTarget = target(city.lat, city.lng, city.zoom.toFloat()),
            )
        }
        if (_state.value.area == null) loadCity(city)
    }

    private suspend fun loadCities(): List<ProviderCity>? {
        if (_state.value.cities.isNotEmpty()) return _state.value.cities
        val answer = find.cities(_state.value.pais)
        if (answer !is StandInAnswer.Ready) return null
        update { copy(cities = answer.value) }
        return answer.value
    }

    private suspend fun loadCity(city: ProviderCity) {
        val mine = ++ticket
        val answer = find.search(
            ProviderQuery(ciudad = city.nombre, pais = _state.value.pais, ramo = currentRamo(), radioKm = 10.0),
        )
        if (mine != ticket) return
        when (answer) {
            is StandInAnswer.Ready -> update {
                val claim = !claimId.isNullOrBlank()
                withRows(answer.value.prestadores, answer.value.truncado).copy(
                    phase = when {
                        claim -> ProviderMapPhase.ClaimMode
                        answer.value.prestadores.isEmpty() -> ProviderMapPhase.Empty
                        else -> ProviderMapPhase.ChooseCity
                    },
                    placement = if (claim) ProviderPlacement.Claim else ProviderPlacement.City,
                    centro = answer.value.centro,
                    radioKm = answer.value.radioKm,
                    ciudad = city.nombre,
                )
            }
            else -> update { keepOrFail() }
        }
    }

    private suspend fun publishNear() {
        val hereLat = lat ?: return
        val hereLng = lng ?: return
        val mine = ++ticket
        val answer = find.search(
            ProviderQuery(lat = hereLat, lng = hereLng, ramo = currentRamo(), radioKm = 10.0),
        )
        if (mine != ticket) return
        when (answer) {
            is StandInAnswer.Ready -> update { nearState(answer.value) }
            else -> update { keepOrFail() }
        }
    }

    private suspend fun loadArea(area: ProviderArea) {
        val mine = ++ticket
        update { copy(area = area) }
        val id = claimId
        val answer: StandInAnswer<Pair<List<Provider>, Boolean>> = if (!id.isNullOrBlank()) {
            when (val claim = find.nearClaim(id, area)) {
                is StandInAnswer.Ready -> StandInAnswer.Ready(claim.value.prestadores to claim.value.truncado)
                else -> StandInAnswer.Failed
            }
        } else {
            val query = ProviderQuery(lat = lat, lng = lng, ramo = currentRamo(), area = area)
            when (val page = find.search(query)) {
                is StandInAnswer.Ready -> StandInAnswer.Ready(page.value.prestadores to page.value.truncado)
                else -> StandInAnswer.Failed
            }
        }
        if (mine != ticket) return
        when (answer) {
            is StandInAnswer.Ready -> update {
                val (rows, truncado) = answer.value
                withRows(rows, truncado).copy(phase = areaPhase(rows))
            }
            else -> update { keepOrFail() }
        }
    }

    private fun loadClaim() {
        val id = claimId ?: return
        claimStarted = true
        job?.cancel()
        areaJob?.cancel()
        job = viewModelScope.launch {
            update { copy(phase = ProviderMapPhase.Loading) }
            when (val answer = find.nearClaim(id)) {
                is StandInAnswer.Ready -> {
                    update { claimState(answer.value) }
                    if (answer.value.sinGeoetiqueta) loadCities()
                }
                else -> update { failed() }
            }
        }
    }

    private fun MapaPrestadoresUi.nearState(page: ProviderPage) =
        withRows(page.prestadores, page.truncado).copy(
            phase = if (page.prestadores.isEmpty()) ProviderMapPhase.Empty else ProviderMapPhase.NearMe,
            placement = ProviderPlacement.Near,
            centro = page.centro,
            radioKm = page.radioKm,
        )

    private fun MapaPrestadoresUi.claimState(page: ClaimProviders): MapaPrestadoresUi {
        val emptyNear = page.prestadores.isEmpty() && !page.sinGeoetiqueta
        val center = page.centro
        return withRows(page.prestadores, page.truncado).copy(
            phase = if (emptyNear) ProviderMapPhase.Empty else ProviderMapPhase.ClaimMode,
            placement = ProviderPlacement.Claim,
            centro = center,
            radioKm = page.radioKm,
            ramo = page.ramoFijo,
            ramoFijo = page.ramoFijo,
            numero = page.numero,
            sinGeoetiqueta = page.sinGeoetiqueta,
            cameraTarget = if (center == null || page.sinGeoetiqueta) cameraTarget else target(center.lat, center.lng, NEAR_ZOOM),
        )
    }

    private fun MapaPrestadoresUi.withRows(rows: List<Provider>, truncado: Boolean): MapaPrestadoresUi {
        val ids = rows.mapTo(hashSetOf()) { it.id }
        return copy(
            providers = rows,
            truncado = truncado,
            loadFailed = false,
            selectedIds = selectedIds.filter { it in ids },
        )
    }

    private fun MapaPrestadoresUi.areaPhase(rows: List<Provider>): ProviderMapPhase = when {
        !claimId.isNullOrBlank() -> if (rows.isEmpty() && !sinGeoetiqueta) ProviderMapPhase.Empty else ProviderMapPhase.ClaimMode
        rows.isEmpty() -> ProviderMapPhase.Empty
        placement == ProviderPlacement.Near -> ProviderMapPhase.NearMe
        else -> ProviderMapPhase.ChooseCity
    }

    private fun MapaPrestadoresUi.keepOrFail(): MapaPrestadoresUi =
        if (providers.isNotEmpty() || area != null) copy(loadFailed = true) else failed()

    private fun MapaPrestadoresUi.failed() = copy(
        phase = ProviderMapPhase.Error,
        providers = emptyList(),
        selectedIds = emptyList(),
    )

    private fun currentRamo(): String? = _state.value.ramoFijo ?: _state.value.ramo

    private fun target(lat: Double, lng: Double, zoom: Float) = CameraTarget(lat, lng, zoom, ++serial)

    private inline fun update(change: MapaPrestadoresUi.() -> MapaPrestadoresUi) {
        _state.value = _state.value.change()
    }

    private companion object {
        const val LOCATION_WAIT_MS = 4_000L
        const val AREA_WAIT_MS = 300L
        const val NEAR_ZOOM = 14f
    }
}
