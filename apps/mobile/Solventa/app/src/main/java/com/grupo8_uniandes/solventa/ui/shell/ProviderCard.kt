package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.rememberVectorPainter
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaIconButton
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun ProviderCard(
    providers: List<Provider>,
    showDistance: Boolean,
    fromEvent: Boolean,
    onOpenProvider: (String) -> Unit,
    onDirections: (Provider) -> Unit,
    onCall: (String) -> Unit,
    onRequestAssistance: (String) -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .padding(SolventaSpacing.s16)
            .testTag("provider_card"),
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 8.dp,
    ) {
        Row(modifier = Modifier.padding(start = SolventaSpacing.s16, top = SolventaSpacing.s8, bottom = SolventaSpacing.s16)) {
            Column(
                modifier = Modifier
                    .weight(1f)
                    .heightIn(max = 360.dp)
                    .verticalScroll(rememberScrollState())
                    .padding(top = SolventaSpacing.s8),
                verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
            ) {
                providers.forEachIndexed { index, provider ->
                    if (index > 0) HorizontalDivider()
                    ProviderDetails(
                        index = index,
                        provider = provider,
                        showDistance = showDistance,
                        fromEvent = fromEvent,
                        onOpenProvider = onOpenProvider,
                        onDirections = onDirections,
                        onCall = onCall,
                        onRequestAssistance = onRequestAssistance,
                    )
                }
            }
            SolventaIconButton(
                icon = rememberVectorPainter(Icons.Filled.Close),
                contentDescription = stringResource(R.string.providers_close_card),
                onClick = onClose,
                testTag = "provider_card_close",
            )
        }
    }
}

@Composable
private fun ProviderDetails(
    index: Int,
    provider: Provider,
    showDistance: Boolean,
    fromEvent: Boolean,
    onOpenProvider: (String) -> Unit,
    onDirections: (Provider) -> Unit,
    onCall: (String) -> Unit,
    onRequestAssistance: (String) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s4)) {
        Text(
            text = provider.nombre,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier
                .heightIn(min = SolventaSpacing.minTouch)
                .clickable(role = Role.Button) { onOpenProvider(provider.id) }
                .semantics { heading() }
                .padding(vertical = SolventaSpacing.s12)
                .testTag("provider_card_name_$index"),
        )
        Text(
            text = stringResource(providerTypeLabel(provider.tipo)),
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        val place = listOf(provider.direccion, provider.barrio).filter { it.isNotBlank() }.joinToString(" · ")
        if (place.isNotBlank()) Text(text = place, style = MaterialTheme.typography.bodyMedium)
        val km = provider.distanciaKm
        if (showDistance && km != null) {
            val label = if (fromEvent) R.string.providers_distance_event else R.string.providers_distance
            Text(
                text = stringResource(label, formatKm(km)),
                style = SolventaTypography.amount,
                modifier = Modifier.testTag("providers_distance_label"),
            )
        }
        Text(text = provider.telefono, style = MaterialTheme.typography.bodyMedium)
        Text(text = provider.horario, style = MaterialTheme.typography.bodyMedium)
        val ramos = provider.ramos.mapNotNull { providerRamoLabel(it) }
        if (ramos.isNotEmpty()) {
            Text(
                text = ramos.map { stringResource(it) }.joinToString(" · "),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Row(
            modifier = Modifier.fillMaxWidth().padding(top = SolventaSpacing.s8, end = SolventaSpacing.s16),
            horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            SolventaButton(
                text = stringResource(R.string.providers_directions),
                style = SolventaButtonStyle.Outlined,
                onClick = { onDirections(provider) },
                modifier = Modifier.weight(1f),
                testTag = "provider_card_directions_$index",
            )
            SolventaButton(
                text = stringResource(R.string.providers_call),
                style = SolventaButtonStyle.Outlined,
                onClick = { onCall(provider.telefono) },
                modifier = Modifier.weight(1f),
                enabled = provider.telefono.isNotBlank(),
                testTag = "provider_card_call_$index",
            )
        }
        SolventaButton(
            text = stringResource(R.string.providers_request),
            style = SolventaButtonStyle.Filled,
            onClick = { onRequestAssistance(provider.id) },
            modifier = Modifier.fillMaxWidth().padding(end = SolventaSpacing.s16),
            testTag = "provider_card_request_$index",
        )
    }
}
