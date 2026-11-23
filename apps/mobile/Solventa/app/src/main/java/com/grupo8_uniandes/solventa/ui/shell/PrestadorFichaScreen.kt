package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun PrestadorFichaScreen(
    provider: Provider?,
    onDirections: () -> Unit,
    onRequestAssistance: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_prestador_ficha"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        if (provider == null) {
            Text(
                text = stringResource(R.string.providers_missing),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("providers_missing"),
            )
            return@Column
        }
        Text(text = provider.nombre, style = MaterialTheme.typography.headlineMedium)
        Fact(stringResource(R.string.providers_type), stringResource(providerTypeLabel(provider.tipo)))
        Fact(stringResource(R.string.providers_address), provider.direccion)
        Fact(stringResource(R.string.providers_city), provider.ciudad)
        Fact(stringResource(R.string.providers_phone), provider.telefono)
        Fact(stringResource(R.string.providers_hours), provider.horario)
        provider.distanciaKm?.let { km ->
            Fact(stringResource(R.string.providers_distance_label), stringResource(R.string.providers_distance, formatKm(km)))
        }
        SolventaButton(
            text = stringResource(R.string.providers_directions),
            style = SolventaButtonStyle.Outlined,
            onClick = onDirections,
            testTag = "action_como_llegar",
        )
        SolventaButton(
            text = stringResource(R.string.providers_request),
            style = SolventaButtonStyle.Filled,
            onClick = onRequestAssistance,
            testTag = "action_pedir_asistencia",
        )
    }
}

@Composable
private fun Fact(label: String, value: String) {
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(text = value, style = MaterialTheme.typography.bodyLarge)
    }
}
