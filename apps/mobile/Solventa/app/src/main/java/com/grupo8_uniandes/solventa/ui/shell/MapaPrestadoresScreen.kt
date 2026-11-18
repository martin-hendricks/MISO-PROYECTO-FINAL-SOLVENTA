package com.grupo8_uniandes.solventa.ui.shell

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.google.android.gms.maps.CameraUpdate
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.LatLngBounds
import com.google.maps.android.compose.CameraMoveStartedReason
import com.google.maps.android.compose.GoogleMap
import com.google.maps.android.compose.MapEffect
import com.google.maps.android.compose.MapProperties
import com.google.maps.android.compose.MapUiSettings
import com.google.maps.android.compose.Marker
import com.google.maps.android.compose.MarkerState
import com.google.maps.android.compose.MapsComposeExperimentalApi
import com.google.maps.android.compose.clustering.Clustering
import com.google.maps.android.compose.clustering.rememberClusterManager
import com.google.maps.android.compose.rememberCameraPositionState
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderArea
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCity
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderType
import com.grupo8_uniandes.solventa.prestadores.MapaPrestadoresUi
import com.grupo8_uniandes.solventa.prestadores.ProviderMapPhase
import com.grupo8_uniandes.solventa.prestadores.ProviderPlacement
import com.grupo8_uniandes.solventa.prestadores.ProviderStack
import com.grupo8_uniandes.solventa.prestadores.ZoomCappedAlgorithm
import com.grupo8_uniandes.solventa.prestadores.stackCoincident
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaChip
import com.grupo8_uniandes.solventa.ui.components.SolventaFloatingAction
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography
import java.util.Locale
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private val providerRamos = listOf(
    "proteccion-dispositivo" to R.string.ramo_proteccion_dispositivo,
    "soat-motocicleta" to R.string.ramo_soat_motocicleta,
    "microseguro-de-vida" to R.string.ramo_microseguro_de_vida,
    "clima-y-vuelos" to R.string.ramo_clima_y_vuelos,
    "vida-hipotecario" to R.string.ramo_vida_hipotecario,
    "pagos" to R.string.ramo_pagos,
    "viaje" to R.string.ramo_viaje,
    "vida-crediticia" to R.string.ramo_vida_crediticia,
)

private val locationPermissions = arrayOf(
    Manifest.permission.ACCESS_FINE_LOCATION,
    Manifest.permission.ACCESS_COARSE_LOCATION,
)

@Composable
fun MapaPrestadoresScreen(
    state: MapaPrestadoresUi,
    onPermission: (Boolean) -> Unit,
    onSelectCity: (ProviderCity) -> Unit,
    onSelectRamo: (String?) -> Unit,
    onOpenProvider: (String) -> Unit,
    modifier: Modifier = Modifier,
    onRetry: () -> Unit = {},
    onReport: () -> Unit = {},
    onSelectProviders: (List<String>) -> Unit = {},
    onCloseCard: () -> Unit = {},
    onCameraIdle: (ProviderArea) -> Unit = {},
    onUserPan: () -> Unit = {},
    onRecenter: () -> Unit = {},
    onDirections: (Provider) -> Unit = {},
    onCall: (String) -> Unit = {},
    onRequestAssistance: (String) -> Unit = {},
    mapSlot: (@Composable (Modifier, () -> Unit) -> Unit)? = null,
) {
    val context = LocalContext.current
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { grants ->
        val granted = grants[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
            grants[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        onPermission(granted)
    }
    LaunchedEffect(Unit) {
        val granted = locationPermissions.any {
            ContextCompat.checkSelfPermission(context, it) == PackageManager.PERMISSION_GRANTED
        }
        onPermission(granted)
        permissionLauncher.launch(locationPermissions)
    }
    val claim = state.placement == ProviderPlacement.Claim
    val showCities = state.cities.isNotEmpty() &&
        state.phase != ProviderMapPhase.Loading &&
        (!claim || state.sinGeoetiqueta)
    val showDistance = state.placement == ProviderPlacement.Near || state.distanceFromEvent
    val wantsMap = state.mapsKey.isNotBlank() &&
        state.cameraTarget != null &&
        (state.phase == ProviderMapPhase.NearMe ||
            state.phase == ProviderMapPhase.ChooseCity ||
            state.phase == ProviderMapPhase.Empty ||
            (state.phase == ProviderMapPhase.ClaimMode && !state.sinGeoetiqueta))
    var mapLoaded by remember { mutableStateOf(false) }
    var mapGaveUp by remember { mutableStateOf(false) }
    var cardHeight by remember { mutableIntStateOf(0) }
    LaunchedEffect(wantsMap) {
        if (!wantsMap) return@LaunchedEffect
        delay(6_000)
        if (!mapLoaded) mapGaveUp = true
    }
    val showMap = wantsMap && mapLoaded && !mapGaveUp
    val selected = state.selected
    BackHandler(enabled = selected.isNotEmpty(), onBack = onCloseCard)
    Box(
        modifier = modifier
            .fillMaxSize()
            .testTag("screen_mapa_prestadores"),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
        ) {
            Header(state)
            if (state.phase != ProviderMapPhase.Loading && state.phase != ProviderMapPhase.CountryEmpty) {
                RamoChips(state = state, onSelectRamo = onSelectRamo)
            }
            if (showCities) {
                CityPicker(cities = state.cities, marked = state.markedCity, onSelectCity = onSelectCity)
            }
            Box(modifier = Modifier.weight(1f).fillMaxWidth()) {
                if (wantsMap && !mapGaveUp) {
                    val onLoaded = { mapLoaded = true }
                    if (mapSlot != null) {
                        mapSlot(Modifier.fillMaxSize(), onLoaded)
                    } else {
                        ProviderGoogleMap(
                            state = state,
                            cardHeight = cardHeight,
                            onSelectProviders = onSelectProviders,
                            onMapClick = onCloseCard,
                            onCameraIdle = onCameraIdle,
                            onUserPan = onUserPan,
                            onRecenter = onRecenter,
                            onMapLoaded = onLoaded,
                            modifier = Modifier.fillMaxSize(),
                        )
                    }
                }
                when {
                    state.phase == ProviderMapPhase.Loading -> {
                        CircularProgressIndicator(
                            modifier = Modifier
                                .align(Alignment.Center)
                                .testTag("providers_loading"),
                        )
                    }
                    state.phase == ProviderMapPhase.Error -> {
                        Column(verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12)) {
                            Text(
                                text = stringResource(R.string.load_failed),
                                style = MaterialTheme.typography.bodyLarge,
                                modifier = Modifier.testTag("providers_error"),
                            )
                            SolventaButton(
                                text = stringResource(R.string.claim_retry),
                                style = SolventaButtonStyle.Outlined,
                                onClick = onRetry,
                                testTag = "providers_retry",
                            )
                        }
                    }
                    state.phase == ProviderMapPhase.CountryEmpty -> {
                        Text(
                            text = stringResource(R.string.providers_country_empty, stringResource(countryName(state.pais))),
                            style = MaterialTheme.typography.bodyLarge,
                            modifier = Modifier.testTag("providers_country_empty"),
                        )
                    }
                    showMap -> MapNotices(
                        state = state,
                        onRetry = onRetry,
                        modifier = Modifier.align(Alignment.TopStart).padding(end = 64.dp),
                    )
                    state.phase == ProviderMapPhase.Empty -> {
                        Text(
                            text = stringResource(R.string.providers_empty),
                            style = MaterialTheme.typography.bodyLarge,
                            modifier = Modifier.testTag("providers_empty"),
                        )
                    }
                    state.providers.isNotEmpty() && selected.isEmpty() -> {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(MaterialTheme.colorScheme.background),
                        ) {
                            ProviderList(
                                rows = state.providers,
                                showDistance = showDistance,
                                title = if (showDistance) stringResource(R.string.providers_nearest) else null,
                                onOpenProvider = onOpenProvider,
                            )
                        }
                    }
                }
                if (selected.isNotEmpty()) {
                    ProviderCard(
                        providers = selected,
                        showDistance = showDistance,
                        fromEvent = state.distanceFromEvent,
                        onOpenProvider = onOpenProvider,
                        onDirections = onDirections,
                        onCall = onCall,
                        onRequestAssistance = onRequestAssistance,
                        onClose = onCloseCard,
                        modifier = Modifier
                            .align(Alignment.BottomCenter)
                            .onSizeChanged { cardHeight = it.height },
                    )
                } else if (showMap && state.providers.isNotEmpty()) {
                    ProviderSheet(
                        state = state,
                        showDistance = showDistance,
                        onOpenProvider = onOpenProvider,
                        onEnableLocation = { permissionLauncher.launch(locationPermissions) },
                        modifier = Modifier.align(Alignment.BottomCenter),
                    )
                }
            }
        }
        if (selected.isEmpty()) {
            SolventaFloatingAction(
                label = stringResource(R.string.action_report_claim),
                icon = painterResource(R.drawable.add),
                onClick = onReport,
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(SolventaSpacing.gutter),
                containerColor = MaterialTheme.colorScheme.error,
                contentColor = MaterialTheme.colorScheme.onError,
            )
        }
    }
}

@Composable
private fun Header(state: MapaPrestadoresUi) {
    val text = when {
        state.placement == ProviderPlacement.Claim && !state.sinGeoetiqueta ->
            stringResource(R.string.providers_claim_header, state.numero.orEmpty())
        state.sinGeoetiqueta ->
            stringResource(R.string.providers_claim_pick, state.numero.orEmpty())
        state.placement == ProviderPlacement.City && state.cities.isNotEmpty() ->
            stringResource(R.string.providers_pick_city)
        else -> null
    }
    if (text != null) {
        Text(
            text = text,
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.testTag("providers_header"),
        )
    }
}

@Composable
private fun RamoChips(state: MapaPrestadoresUi, onSelectRamo: (String?) -> Unit) {
    val locked = state.ramoFijo
    Row(
        modifier = Modifier.horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
    ) {
        SolventaChip(
            label = stringResource(R.string.claim_chip_todos),
            selected = locked == null && state.ramo == null,
            onClick = { onSelectRamo(null) },
            modifier = Modifier.heightIn(min = SolventaSpacing.minTouch),
            enabled = locked == null,
            showSelectionIcon = false,
            labelStyle = SolventaTypography.amount,
            testTag = "ramo_todos",
        )
        providerRamos.forEach { (code, label) ->
            val fixed = locked == code
            SolventaChip(
                label = stringResource(label),
                selected = state.ramo == code || fixed,
                onClick = { onSelectRamo(code) },
                modifier = Modifier.heightIn(min = SolventaSpacing.minTouch),
                enabled = locked == null || fixed,
                showSelectionIcon = false,
                labelStyle = SolventaTypography.amount,
                testTag = "ramo_$code",
            )
        }
    }
}

@Composable
private fun CityPicker(cities: List<ProviderCity>, marked: String?, onSelectCity: (ProviderCity) -> Unit) {
    Row(
        modifier = Modifier
            .horizontalScroll(rememberScrollState())
            .testTag("providers_cities"),
        horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
    ) {
        cities.forEach { city ->
            SolventaChip(
                label = city.nombre,
                selected = marked == city.nombre,
                onClick = { onSelectCity(city) },
                modifier = Modifier.heightIn(min = SolventaSpacing.minTouch),
                showSelectionIcon = false,
                labelStyle = SolventaTypography.amount,
                testTag = "city_${city.nombre}",
            )
        }
    }
}

@Composable
private fun MapNotices(state: MapaPrestadoresUi, onRetry: () -> Unit, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.padding(SolventaSpacing.s8),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
    ) {
        if (state.truncado) Notice(stringResource(R.string.providers_truncated), "providers_truncated")
        if (state.phase == ProviderMapPhase.Empty) Notice(stringResource(R.string.providers_empty), "providers_empty")
        if (state.loadFailed) {
            Surface(shape = RoundedCornerShape(12.dp), shadowElevation = 4.dp) {
                Row(
                    modifier = Modifier.padding(start = SolventaSpacing.s12),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
                ) {
                    Text(
                        text = stringResource(R.string.load_failed),
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.weight(1f, fill = false).testTag("providers_error"),
                    )
                    SolventaButton(
                        text = stringResource(R.string.claim_retry),
                        style = SolventaButtonStyle.Text,
                        onClick = onRetry,
                        testTag = "providers_retry",
                    )
                }
            }
        }
    }
}

@Composable
private fun Notice(text: String, tag: String) {
    Surface(shape = RoundedCornerShape(12.dp), shadowElevation = 4.dp) {
        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier
                .padding(horizontal = SolventaSpacing.s12, vertical = SolventaSpacing.s8)
                .testTag(tag),
        )
    }
}

@Composable
private fun ProviderSheet(
    state: MapaPrestadoresUi,
    showDistance: Boolean,
    onOpenProvider: (String) -> Unit,
    onEnableLocation: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val city = state.placement == ProviderPlacement.City
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(max = 280.dp)
            .testTag("providers_sheet"),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 8.dp,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s8)) {
            ProviderList(
                rows = state.providers.take(3),
                showDistance = showDistance,
                title = when {
                    showDistance -> stringResource(R.string.providers_nearest)
                    city && state.ciudad != null -> stringResource(R.string.providers_in_city, state.ciudad)
                    else -> null
                },
                onOpenProvider = onOpenProvider,
                modifier = Modifier.weight(1f, fill = false),
            )
            if (city && !state.canRecenter) {
                SolventaButton(
                    text = stringResource(R.string.providers_enable_location),
                    style = SolventaButtonStyle.Outlined,
                    onClick = onEnableLocation,
                    testTag = "providers_enable_location",
                )
            }
        }
    }
}

@OptIn(MapsComposeExperimentalApi::class)
@Composable
private fun ProviderGoogleMap(
    state: MapaPrestadoresUi,
    cardHeight: Int,
    onSelectProviders: (List<String>) -> Unit,
    onMapClick: () -> Unit,
    onCameraIdle: (ProviderArea) -> Unit,
    onUserPan: () -> Unit,
    onRecenter: () -> Unit,
    onMapLoaded: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val start = state.cameraTarget ?: return
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val camera = rememberCameraPositionState {
        position = CameraPosition.fromLatLngZoom(LatLng(start.lat, start.lng), start.zoom)
    }
    val idle by rememberUpdatedState(onCameraIdle)
    val pan by rememberUpdatedState(onUserPan)
    val select by rememberUpdatedState(onSelectProviders)
    var mapHeight by remember { mutableIntStateOf(0) }
    var loaded by remember { mutableStateOf(false) }
    val margin = with(LocalDensity.current) { SolventaSpacing.s16.roundToPx() }
    val reportIdle = { camera.projection?.visibleRegion?.latLngBounds?.toArea()?.let(idle) }
    val move: (() -> CameraUpdate) -> Unit = { update -> if (loaded) scope.launch { camera.animate(update()) } }
    LaunchedEffect(state.cameraTarget, loaded) {
        val target = state.cameraTarget ?: return@LaunchedEffect
        if (loaded) camera.animate(CameraUpdateFactory.newLatLngZoom(LatLng(target.lat, target.lng), target.zoom))
    }
    LaunchedEffect(camera) {
        snapshotFlow { camera.isMoving }.collect { moving ->
            when {
                !moving -> reportIdle()
                camera.cameraMoveStartedReason == CameraMoveStartedReason.GESTURE -> pan()
            }
        }
    }
    LaunchedEffect(state.selectedIds, cardHeight) {
        val chosen = state.selected.firstOrNull() ?: return@LaunchedEffect
        val point = camera.projection?.toScreenLocation(LatLng(chosen.lat, chosen.lng)) ?: return@LaunchedEffect
        val limit = mapHeight - cardHeight - margin
        if (loaded && cardHeight > 0 && point.y > limit) {
            camera.animate(CameraUpdateFactory.scrollBy(0f, (point.y - limit).toFloat()))
        }
    }
    val stacks = remember(state.providers, state.selectedIds) {
        stackCoincident(state.providers).map { stack ->
            stack.copy(selected = stack.ids.any { it in state.selectedIds })
        }
    }
    Box(modifier = modifier.onSizeChanged { mapHeight = it.height }) {
        GoogleMap(
            modifier = Modifier.fillMaxSize().testTag("providers_map"),
            cameraPositionState = camera,
            properties = MapProperties(minZoomPreference = 5f, maxZoomPreference = 18f),
            uiSettings = MapUiSettings(
                rotationGesturesEnabled = false,
                tiltGesturesEnabled = false,
                zoomControlsEnabled = false,
                myLocationButtonEnabled = false,
                mapToolbarEnabled = false,
            ),
            onMapClick = { onMapClick() },
            onMapLoaded = {
                loaded = true
                onMapLoaded()
                reportIdle()
            },
        ) {
            val manager = rememberClusterManager<ProviderStack>()
            MapEffect(manager) { map ->
                val clusters = manager ?: return@MapEffect
                clusters.renderer = ProviderClusterRenderer(context, map, clusters)
                clusters.algorithm = ZoomCappedAlgorithm()
                clusters.setOnClusterClickListener { cluster ->
                    val bounds = LatLngBounds.builder().apply { cluster.items.forEach { include(it.position) } }.build()
                    move { CameraUpdateFactory.newLatLngBounds(bounds, margin * 4) }
                    true
                }
                clusters.setOnClusterItemClickListener { stack ->
                    select(stack.ids)
                    true
                }
            }
            if (manager != null) Clustering(items = stacks, clusterManager = manager)
            val centro = state.centro
            if (state.distanceFromEvent && centro != null) {
                Marker(
                    state = MarkerState(position = LatLng(centro.lat, centro.lng)),
                    title = state.numero,
                    zIndex = 2f,
                )
            }
            if (state.canRecenter && centro != null && state.placement == ProviderPlacement.Near) {
                Marker(
                    state = MarkerState(position = LatLng(centro.lat, centro.lng)),
                    title = stringResource(R.string.providers_my_location),
                    icon = BitmapDescriptorFactory.defaultMarker(BitmapDescriptorFactory.HUE_AZURE),
                    zIndex = 2f,
                )
            }
        }
        Column(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(SolventaSpacing.s8),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
        ) {
            MapButton(Icons.Filled.Add, stringResource(R.string.providers_zoom_in), "providers_zoom_in") {
                move { CameraUpdateFactory.zoomIn() }
            }
            MapButton(Icons.Filled.Remove, stringResource(R.string.providers_zoom_out), "providers_zoom_out") {
                move { CameraUpdateFactory.zoomOut() }
            }
            if (state.canRecenter) {
                MapButton(Icons.Filled.MyLocation, stringResource(R.string.providers_my_location), "providers_my_location", onRecenter)
            }
        }
    }
}

@Composable
private fun MapButton(icon: ImageVector, label: String, tag: String, onClick: () -> Unit) {
    Surface(shape = CircleShape, shadowElevation = 4.dp, color = MaterialTheme.colorScheme.surface) {
        IconButton(onClick = onClick, modifier = Modifier.size(SolventaSpacing.minTouch).testTag(tag)) {
            Icon(imageVector = icon, contentDescription = label, tint = MaterialTheme.colorScheme.onSurface)
        }
    }
}

private fun LatLngBounds.toArea(): ProviderArea? {
    if (southwest.longitude > northeast.longitude) return null
    return ProviderArea(
        norte = northeast.latitude,
        sur = southwest.latitude,
        este = northeast.longitude,
        oeste = southwest.longitude,
    )
}

@Composable
private fun ProviderList(
    rows: List<Provider>,
    showDistance: Boolean,
    title: String?,
    onOpenProvider: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .testTag("providers_list"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        if (!title.isNullOrBlank()) {
            Text(text = title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.testTag("providers_list_title"))
        }
        rows.forEachIndexed { index, provider ->
            ProviderRow(index, provider, showDistance, onOpenProvider)
        }
    }
}

@Composable
private fun ProviderRow(
    index: Int,
    provider: Provider,
    showDistance: Boolean,
    onOpenProvider: (String) -> Unit,
) {
    SolventaCard(
        onClick = { onOpenProvider(provider.id) },
        outlined = true,
        testTag = "action_open_provider_$index",
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = provider.nombre,
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.weight(1f),
            )
            Icon(
                painter = painterResource(R.drawable.chevron_right),
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        val place = listOf(provider.direccion, provider.barrio, provider.ciudad)
            .filter { it.isNotBlank() }
            .joinToString(" · ")
        if (place.isNotBlank()) {
            Text(
                text = place,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        if (showDistance && provider.distanciaKm != null) {
            Text(
                text = stringResource(R.string.providers_distance, formatKm(provider.distanciaKm)),
                style = SolventaTypography.amount,
            )
        }
    }
}

internal fun formatKm(km: Double): String =
    String.format(Locale.US, "%.1f", km).replace('.', ',')

internal fun providerRamoLabel(code: String): Int? = providerRamos.firstOrNull { it.first == code }?.second

internal fun countryName(pais: String): Int = when (pais) {
    "MX" -> R.string.country_name_mx
    "CL" -> R.string.country_name_cl
    "PE" -> R.string.country_name_pe
    else -> R.string.country_name_co
}

internal fun providerTypeLabel(tipo: ProviderType): Int = when (tipo) {
    ProviderType.SERVICIO_TECNICO -> R.string.provider_type_servicio_tecnico
    ProviderType.TALLER_MOTOS -> R.string.provider_type_taller_motos
    ProviderType.IPS_URGENCIAS -> R.string.provider_type_ips_urgencias
    ProviderType.GRUA -> R.string.provider_type_grua
    ProviderType.ASISTENCIA_VIAJERO -> R.string.provider_type_asistencia_viajero
    ProviderType.PUNTO_AEROPUERTO -> R.string.provider_type_punto_aeropuerto
    ProviderType.IPS_EXAMENES -> R.string.provider_type_ips_examenes
    ProviderType.FUNERARIA -> R.string.provider_type_funeraria
    ProviderType.CENTRO_ATENCION -> R.string.provider_type_centro_atencion
}
