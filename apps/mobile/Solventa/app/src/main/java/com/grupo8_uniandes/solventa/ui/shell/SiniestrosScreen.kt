package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaChip
import com.grupo8_uniandes.solventa.ui.components.SolventaFloatingAction
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun SiniestrosScreen(
    claims: List<ClaimSummary>,
    onOpenClaim: (String) -> Unit,
    onReport: () -> Unit = {},
    failed: Boolean = false,
    chip: ClaimStatus? = null,
    onChip: (ClaimStatus?) -> Unit = {},
    filterMiss: Boolean = false,
    onRetry: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .testTag("screen_siniestros"),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
        ) {
            ClaimChips(chip = chip, onChip = onChip)
            if (failed) {
                Text(
                    text = stringResource(R.string.load_failed),
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier
                        .testTag("load_failed")
                        .semantics { liveRegion = LiveRegionMode.Polite },
                )
                SolventaButton(
                    text = stringResource(R.string.claim_retry),
                    style = SolventaButtonStyle.Outlined,
                    onClick = onRetry,
                    testTag = "claim_retry",
                )
            }
            if (claims.isEmpty() && !failed) {
                Text(
                    text = stringResource(if (filterMiss) R.string.claim_list_none else R.string.claim_list_empty),
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.testTag(if (filterMiss) "claim_list_none" else "claim_list_empty"),
                )
            }
            claims.forEach { claim ->
                ClaimCard(claim = claim, onOpenClaim = onOpenClaim)
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
internal fun ClaimChips(
    chip: ClaimStatus? = null,
    onChip: (ClaimStatus?) -> Unit = {},
) {
    Row(
        modifier = Modifier.horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        SolventaChip(
            label = stringResource(R.string.claim_chip_todos),
            selected = chip == null,
            onClick = { onChip(null) },
            showSelectionIcon = false,
            labelStyle = SolventaTypography.amount,
            testTag = "chip_todos",
        )
        ClaimStatus.entries.forEach { status ->
            SolventaChip(
                label = stringResource(status.chipLabel()),
                selected = chip == status,
                onClick = { onChip(status) },
                showSelectionIcon = false,
                labelStyle = SolventaTypography.amount,
                testTag = "chip_${status.name.lowercase()}",
            )
        }
    }
}

private fun ClaimStatus.chipLabel(): Int = when (this) {
    ClaimStatus.RECIBIDO -> R.string.claim_chip_recibido
    ClaimStatus.EN_EVALUACION -> R.string.claim_chip_en_evaluacion
    ClaimStatus.DECIDIDO -> R.string.claim_chip_decidido
    ClaimStatus.ENRUTADO -> R.string.claim_chip_enrutado
    ClaimStatus.PAGADO -> R.string.claim_chip_pagado
}

@Composable
private fun ClaimCard(
    claim: ClaimSummary,
    onOpenClaim: (String) -> Unit,
) {
    SolventaCard(
        onClick = { onOpenClaim(claim.id) },
        outlined = true,
        testTag = "action_open_claim_${claim.siniestroId}",
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = claim.siniestroId,
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.weight(1f),
            )
            Icon(
                painter = painterResource(R.drawable.chevron_right),
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Text(
            text = claim.whatHappened(),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = claim.statusWords(),
            style = SolventaTypography.amount,
        )
    }
}
