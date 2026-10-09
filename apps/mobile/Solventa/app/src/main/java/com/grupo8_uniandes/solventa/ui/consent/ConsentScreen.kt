package com.grupo8_uniandes.solventa.ui.consent

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
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
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaSwitch
import com.grupo8_uniandes.solventa.ui.components.SolventaTopBar
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun ConsentScreen(
    switchOn: Boolean,
    confirmEnabled: Boolean,
    onSwitch: (Boolean) -> Unit,
    onConfirm: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .testTag("screen_consentimiento"),
    ) {
        SolventaTopBar(
            title = stringResource(R.string.consent_title),
            showBack = true,
            onBack = onBack,
        )
        Column(
            modifier = Modifier
                .verticalScroll(rememberScrollState())
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
        ) {
            ConsentBody(
                switchOn = switchOn,
                confirmEnabled = confirmEnabled,
                onSwitch = onSwitch,
                onConfirm = onConfirm,
            )
        }
    }
}

@Composable
fun ConsentBody(
    switchOn: Boolean,
    confirmEnabled: Boolean,
    onSwitch: (Boolean) -> Unit,
    onConfirm: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.consent_heading),
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Text(
            text = stringResource(R.string.consent_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        SolventaSwitch(
            label = stringResource(R.string.consent_heading),
            checked = switchOn,
            onCheckedChange = onSwitch,
            showLabel = false,
        )
        SolventaButton(
            text = stringResource(R.string.action_aceptar_continuar),
            style = SolventaButtonStyle.Filled,
            onClick = onConfirm,
            enabled = confirmEnabled,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_aceptar_continuar",
        )
    }
}
