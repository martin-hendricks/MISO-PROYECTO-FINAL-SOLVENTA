package com.grupo8_uniandes.solventa.ui.shell

import android.Manifest
import android.content.pm.PackageManager
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.LatLng
import com.google.maps.android.compose.GoogleMap
import com.google.maps.android.compose.Marker
import com.google.maps.android.compose.MarkerState
import com.google.maps.android.compose.rememberCameraPositionState
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderType
import com.grupo8_uniandes.solventa.prestadores.MapaPrestadoresUi
import com.grupo8_uniandes.solventa.prestadores.ProviderMapPhase
import com.grupo8_uniandes.solventa.prestadores.ProviderPlacement
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaChip
import com.grupo8_uniandes.solventa.ui.components.SolventaFloatingAction
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography
import java.util.Locale
import kotlinx.coroutines.delay

internal val providerCities = listOf("Bogotá", "Medellín", "Chía")

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

@Composable
fun MapaPrestadoresScreen(
    state: MapaPrestadoresUi,
    onPermission: (Boolean) -> Unit,
    onSelectCity: (String) -> Unit,
    onSelectRamo: (String?) -> Unit,
    onOpenProvider: (String) -> Unit,
    onRetry: () -> Unit = {},
    onReport: () -> Unit = {},
    modifier: Modifier = Modifier,
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
        val fine = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION,
        ) == PackageManager.PERMISSION_GRANTED
        val coarse = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_COARSE_LOCATION,
        ) == PackageManager.PERMISSION_GRANTED
        onPermission(fine || coarse)
        permissionLauncher.launch(
            arrayOf(
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION,
            ),
        )
    }
    val showCities = state.phase == ProviderMapPhase.ChooseCity ||
        state.phase == ProviderMapPhase.Empty ||
        (state.phase == ProviderMapPhase.ClaimMode && state.sinGeoetiqueta) ||
        (state.phase == ProviderMapPhase.Error && state.placement == ProviderPlacement.City)
    val showDistance = state.placement == ProviderPlacement.Near ||
        (state.placement == ProviderPlacement.Claim && !state.sinGeoetiqueta)
    val wantsMap = state.mapsKey.isNotBlank() &&
        state.centro != null &&
        state.providers.isNotEmpty() &&
        (state.phase == ProviderMapPhase.NearMe ||
            state.phase == ProviderMapPhase.ChooseCity ||
            (state.phase == ProviderMapPhase.ClaimMode && !state.sinGeoetiqueta))
    var mapLoaded by remember(state.centro, state.providers) { mutableStateOf(false) }
    var mapGaveUp by remember(state.centro, state.providers) { mutableStateOf(false) }
    LaunchedEffect(wantsMap, state.centro, state.providers) {
        if (!wantsMap) return@LaunchedEffect
        delay(6_000)
        if (!mapLoaded) mapGaveUp = true
    }
    val showMap = wantsMap && mapLoaded && !mapGaveUp
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
            if (state.phase != ProviderMapPhase.Loading) {
                RamoChips(state = state, onSelectRamo = onSelectRamo)
            }
            if (showCities) {
                CityPicker(selected = state.ciudad, onSelectCity = onSelectCity)
            }
            Box(modifier = Modifier.weight(1f).fillMaxWidth()) {
                if (wantsMap && !mapGaveUp) {
                    ProviderGoogleMap(
                        state = state,
                        onOpenProvider = onOpenProvider,
                        onMapLoaded = { mapLoaded = true },
                        modifier = Modifier.fillMaxSize(),
                    )
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
                    state.phase == ProviderMapPhase.Empty -> {
                        Text(
                            text = stringResource(R.string.providers_empty),
                            style = MaterialTheme.typography.bodyLarge,
                            modifier = Modifier.testTag("providers_empty"),
                        )
                    }
                    showMap -> Unit
                    state.providers.isNotEmpty() -> {
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
                if (showMap) {
                    Surface(
                        modifier = Modifier
                            .align(Alignment.BottomCenter)
                            .fillMaxWidth()
                            .heightIn(max = 280.dp),
                        color = MaterialTheme.colorScheme.surface,
                        shadowElevation = 8.dp,
                    ) {
                        ProviderList(
                            rows = state.providers.take(3),
                            showDistance = showDistance,
                            title = if (showDistance) stringResource(R.string.providers_nearest) else state.ciudad,
                            onOpenProvider = onOpenProvider,
                        )
                    }
                }
            }
        }
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

@Composable
private fun Header(state: MapaPrestadoresUi) {
    val text = when {
        state.placement == ProviderPlacement.Near ->
            stringResource(R.string.providers_near_header, formatRadio(state.radioKm))
        state.placement == ProviderPlacement.Claim && !state.sinGeoetiqueta ->
            stringResource(R.string.providers_claim_header, state.numero.orEmpty())
        state.sinGeoetiqueta ->
            stringResource(R.string.providers_claim_pick, state.numero.orEmpty())
        state.phase == ProviderMapPhase.ChooseCity || state.placement == ProviderPlacement.City ->
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
                enabled = locked == null || fixed,
                showSelectionIcon = false,
                labelStyle = SolventaTypography.amount,
                testTag = "ramo_$code",
            )
        }
    }
}

@Composable
private fun CityPicker(selected: String?, onSelectCity: (String) -> Unit) {
    Row(
        modifier = Modifier
            .horizontalScroll(rememberScrollState())
            .testTag("providers_cities"),
        horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
    ) {
        providerCities.forEach { city ->
            SolventaChip(
                label = city,
                selected = selected == city,
                onClick = { onSelectCity(city) },
                showSelectionIcon = false,
                labelStyle = SolventaTypography.amount,
                testTag = "city_$city",
            )
        }
    }
}

@Composable
private fun ProviderGoogleMap(
    state: MapaPrestadoresUi,
    onOpenProvider: (String) -> Unit,
    onMapLoaded: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val centro = state.centro ?: return
    val camera = rememberCameraPositionState {
        position = CameraPosition.fromLatLngZoom(LatLng(centro.lat, centro.lng), 13f)
    }
    LaunchedEffect(centro.lat, centro.lng) {
        camera.position = CameraPosition.fromLatLngZoom(LatLng(centro.lat, centro.lng), 13f)
    }
    GoogleMap(
        modifier = modifier.testTag("providers_map"),
        cameraPositionState = camera,
        onMapLoaded = onMapLoaded,
    ) {
        state.providers.forEach { provider ->
            Marker(
                state = MarkerState(position = LatLng(provider.lat, provider.lng)),
                title = provider.nombre,
                onClick = {
                    onOpenProvider(provider.id)
                    true
                },
            )
        }
    }
}

@Composable
private fun ProviderList(
    rows: List<Provider>,
    showDistance: Boolean,
    title: String?,
    onOpenProvider: (String) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .testTag("providers_list"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        if (!title.isNullOrBlank()) {
            Text(text = title, style = MaterialTheme.typography.titleMedium)
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

private fun formatRadio(km: Double): String =
    if (km % 1.0 == 0.0) km.toInt().toString() else formatKm(km)

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
