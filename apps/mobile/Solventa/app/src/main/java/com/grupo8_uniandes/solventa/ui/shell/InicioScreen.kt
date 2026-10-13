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
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun InicioScreen(
    state: HomeUiState,
    onNewQuote: () -> Unit,
    onAcceptOffer: (String) -> Unit = {},
    onOpenPolicy: (String) -> Unit = {},
    onOpenClaim: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val panel = state.panel
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_inicio"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.destination_inicio),
            style = MaterialTheme.typography.headlineMedium,
        )
        panel.offerId?.let { offerId ->
            SolventaCard(testTag = "home_offer") {
                Text(text = offerId, style = SolventaTypography.amount)
            }
            SolventaButton(
                text = stringResource(R.string.action_accept_offer),
                style = SolventaButtonStyle.Filled,
                onClick = { onAcceptOffer(offerId) },
                testTag = "action_accept_offer",
            )
            SolventaButton(
                text = stringResource(R.string.action_new_quote),
                style = SolventaButtonStyle.Tonal,
                onClick = onNewQuote,
                testTag = "action_new_quote",
            )
        }
        if (panel.offerId == null) {
            SolventaButton(
                text = stringResource(R.string.action_new_quote),
                style = SolventaButtonStyle.Filled,
                onClick = onNewQuote,
                testTag = "action_new_quote",
            )
        }
        panel.policyId?.let { policyId ->
            SolventaCard(
                onClick = { onOpenPolicy(policyId) },
                testTag = "home_policy",
            ) {
                Text(
                    text = stringResource(R.string.policy_detail_title),
                    style = MaterialTheme.typography.bodyLarge,
                )
                Text(text = policyId, style = SolventaTypography.amount)
            }
        }
        panel.claimId?.let { claimId ->
            SolventaCard(
                onClick = { onOpenClaim(claimId) },
                testTag = "home_claim",
            ) {
                Text(text = claimId, style = SolventaTypography.amount)
            }
        }
        if (panel.vidaCrediticia) {
            SolventaCard(
                onClick = {},
                testTag = "home_vida_crediticia",
            ) {
                Text(
                    text = stringResource(R.string.home_vida_crediticia),
                    style = MaterialTheme.typography.bodyLarge,
                )
            }
        }
    }
}
