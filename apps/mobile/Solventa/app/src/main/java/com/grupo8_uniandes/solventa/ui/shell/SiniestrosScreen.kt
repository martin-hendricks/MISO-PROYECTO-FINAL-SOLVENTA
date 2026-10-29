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
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun SiniestrosScreen(
    claims: List<ClaimSummary>,
    onOpenClaim: (String) -> Unit,
    failed: Boolean = false,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_siniestros"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.destination_siniestros),
            style = MaterialTheme.typography.headlineMedium,
        )
        if (failed) {
            Text(
                text = stringResource(R.string.load_failed),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("load_failed"),
            )
        }
        claims.forEach { claim ->
            SolventaCard(
                onClick = { onOpenClaim(claim.siniestroId) },
                testTag = "action_open_claim_${claim.siniestroId}",
            ) {
                Text(text = claim.siniestroId, style = SolventaTypography.amount)
                Text(text = claim.ramo, style = MaterialTheme.typography.bodyLarge)
                Text(text = claim.resumen, style = MaterialTheme.typography.bodyMedium)
                Text(text = claim.estado.wireName(), style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

private fun ClaimStatus.wireName(): String = name.lowercase()
