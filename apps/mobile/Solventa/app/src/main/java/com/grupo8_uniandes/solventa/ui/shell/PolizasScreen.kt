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
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
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
    failed: Boolean = false,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_polizas"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.destination_polizas),
            style = MaterialTheme.typography.headlineMedium,
        )
        SolventaButton(
            text = stringResource(R.string.action_new_quote),
            style = SolventaButtonStyle.Filled,
            onClick = onNewQuote,
            testTag = "action_new_quote",
        )
        if (failed) {
            Text(
                text = stringResource(R.string.load_failed),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("load_failed"),
            )
        }
        policies.forEach { policy ->
            SolventaCard(
                onClick = { onOpenPolicy(policy.numero) },
                testTag = "action_open_policy_${policy.numero}",
            ) {
                Text(text = policy.numero, style = SolventaTypography.amount)
                Text(text = policy.ramo, style = MaterialTheme.typography.bodyLarge)
                Text(text = policy.resumen, style = MaterialTheme.typography.bodyMedium)
                Text(text = policy.estado, style = MaterialTheme.typography.bodyMedium)
                Text(text = policy.venceEn, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
