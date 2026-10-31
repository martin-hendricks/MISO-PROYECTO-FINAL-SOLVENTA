package com.grupo8_uniandes.solventa.ui.shell

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
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.domain.bff.issuance.listBody
import com.grupo8_uniandes.solventa.domain.bff.issuance.listMeta
import com.grupo8_uniandes.solventa.policy.WalletPhase
import com.grupo8_uniandes.solventa.ui.components.SolventaBanner
import com.grupo8_uniandes.solventa.ui.components.SolventaBannerStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun PolizasScreen(
    policies: List<WalletEntry>,
    onOpenPolicy: (String) -> Unit,
    onNewQuote: () -> Unit,
    phase: WalletPhase = if (policies.isEmpty()) WalletPhase.Failed else WalletPhase.Ready,
    notice: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val showEmpty = policies.isEmpty() && phase != WalletPhase.Pending
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_polizas"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.destination_polizas),
            style = MaterialTheme.typography.headlineMedium,
        )
        policies.forEach { policy ->
            SolventaCard(
                onClick = { onOpenPolicy(policy.numero) },
                testTag = "action_open_policy_${policy.numero}",
            ) {
                Text(text = policy.numero, style = SolventaTypography.amount)
                Text(text = listBody(policy), style = MaterialTheme.typography.bodyLarge)
                Text(text = listMeta(policy), style = SolventaTypography.amount)
            }
        }
        if (policies.isNotEmpty()) {
            SolventaBanner(
                message = stringResource(R.string.policy_operator_note),
                style = SolventaBannerStyle.Info,
            )
        }
        if (notice) {
            Text(
                text = stringResource(R.string.policy_sync_notice),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.testTag("policy_sync_notice"),
            )
        }
        if (showEmpty) {
            Text(
                text = stringResource(R.string.policy_empty),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.fillMaxWidth(),
            )
            SolventaButton(
                text = stringResource(R.string.action_request_quote),
                style = SolventaButtonStyle.Outlined,
                onClick = onNewQuote,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_request_quote",
            )
        }
    }
}
