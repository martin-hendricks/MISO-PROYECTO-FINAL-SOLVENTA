package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun SiniestroDetalleScreen(
    claimId: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    lines: List<String> = emptyList(),
    missing: Boolean = false,
    failed: Boolean = false,
    onRetry: () -> Unit = {},
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SolventaSpacing.gutter)
            .testTag("screen_siniestro_detalle"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.destination_siniestros),
            style = MaterialTheme.typography.headlineMedium,
        )
        Text(
            text = claimId,
            style = SolventaTypography.amount,
        )
        lines.forEach { line ->
            Text(text = line, style = MaterialTheme.typography.bodyLarge)
        }
        if (missing) {
            Text(
                text = stringResource(R.string.claim_not_found),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("claim_not_found"),
            )
        }
        if (failed) {
            Text(
                text = stringResource(R.string.load_failed),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("claim_detail_failed"),
            )
            SolventaButton(
                text = stringResource(R.string.claim_retry),
                style = SolventaButtonStyle.Outlined,
                onClick = onRetry,
                testTag = "claim_detail_retry",
            )
        }
        SolventaButton(
            text = stringResource(R.string.action_back),
            style = SolventaButtonStyle.Outlined,
            onClick = onBack,
            testTag = "action_siniestro_volver",
        )
    }
}
