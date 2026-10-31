package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaStatus
import com.grupo8_uniandes.solventa.ui.components.SolventaStatusIcon
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun ConfirmacionAvisoScreen(
    siniestroId: String,
    onMyClaims: () -> Unit,
    onHome: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_confirmacion_aviso"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        SolventaStatusIcon(
            status = SolventaStatus.Success,
            word = stringResource(R.string.claim_sent_heading),
            icon = painterResource(R.drawable.status_success),
            modifier = Modifier.align(Alignment.Start),
        )
        Text(
            text = stringResource(R.string.claim_sent_body, siniestroId),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        SolventaButton(
            text = stringResource(R.string.claim_sent_list),
            style = SolventaButtonStyle.Filled,
            onClick = onMyClaims,
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_my_notices",
        )
        SolventaButton(
            text = stringResource(R.string.claim_sent_home),
            style = SolventaButtonStyle.Tonal,
            onClick = onHome,
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_go_home",
        )
    }
}
