package com.grupo8_uniandes.solventa.ui.shell

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
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaChip
import com.grupo8_uniandes.solventa.ui.components.SolventaFloatingAction
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun SiniestrosScreen(
    claims: List<ClaimSummary>,
    onOpenClaim: (String) -> Unit,
    onOpenCatalog: () -> Unit,
    failed: Boolean = false,
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
            ClaimChips(onOpenCatalog = onOpenCatalog)
            if (failed) {
                Text(
                    text = stringResource(R.string.load_failed),
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.testTag("load_failed"),
                )
            }
            claims.forEach { claim ->
                ClaimCard(claim = claim, onOpenClaim = onOpenClaim)
            }
        }
        SolventaFloatingAction(
            label = stringResource(R.string.action_report_claim),
            icon = painterResource(R.drawable.add),
            onClick = {},
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(SolventaSpacing.gutter),
            containerColor = MaterialTheme.colorScheme.error,
            contentColor = MaterialTheme.colorScheme.onError,
        )
    }
}

@Composable
internal fun ClaimChips(onOpenCatalog: (() -> Unit)? = null) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        SolventaChip(
            label = stringResource(R.string.claim_chip_todos),
            selected = true,
            onClick = {},
            showSelectionIcon = false,
            labelStyle = SolventaTypography.amount,
            testTag = "chip_todos",
        )
        SolventaChip(
            label = stringResource(R.string.claim_chip_en_evaluacion),
            selected = false,
            onClick = {},
            showSelectionIcon = false,
            labelStyle = SolventaTypography.amount,
            testTag = "chip_en_evaluacion",
        )
        SolventaChip(
            label = stringResource(R.string.claim_chip_pagado),
            selected = false,
            onClick = {},
            showSelectionIcon = false,
            labelStyle = SolventaTypography.amount,
            testTag = "chip_pagado",
        )
        if (onOpenCatalog != null) {
            IconButton(
                onClick = onOpenCatalog,
                modifier = Modifier.testTag("action_open_catalog"),
            ) {
                Icon(
                    painter = painterResource(R.drawable.chevron_right),
                    contentDescription = stringResource(R.string.destination_siniestros),
                )
            }
        }
    }
}

@Composable
private fun ClaimCard(
    claim: ClaimSummary,
    onOpenClaim: (String) -> Unit,
) {
    SolventaCard(
        onClick = { onOpenClaim(claim.siniestroId) },
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
