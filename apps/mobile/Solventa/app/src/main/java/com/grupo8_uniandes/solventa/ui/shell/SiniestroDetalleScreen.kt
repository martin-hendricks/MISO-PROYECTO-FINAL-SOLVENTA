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
        SolventaButton(
            text = stringResource(R.string.action_back),
            style = SolventaButtonStyle.Outlined,
            onClick = onBack,
            testTag = "action_siniestro_volver",
        )
    }
}
