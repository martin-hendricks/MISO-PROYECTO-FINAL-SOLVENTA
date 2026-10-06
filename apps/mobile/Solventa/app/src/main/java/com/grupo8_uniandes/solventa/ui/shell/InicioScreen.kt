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
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SolventaSpacing.gutter)
            .testTag("screen_inicio"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.destination_inicio),
            style = MaterialTheme.typography.headlineMedium,
        )
        Text(
            text = stringResource(R.string.sample_policy_id),
            style = SolventaTypography.amount,
            modifier = Modifier.testTag("sample_policy_id"),
        )
        SolventaButton(
            text = stringResource(R.string.action_new_quote),
            style = SolventaButtonStyle.Filled,
            onClick = onNewQuote,
        )
        state.summary.offer?.let { offer ->
            SolventaCard {
                Text(text = offer.label, style = MaterialTheme.typography.bodyLarge)
            }
        }
        state.summary.policy?.let { policy ->
            SolventaCard {
                Text(text = policy.policyId, style = SolventaTypography.amount)
            }
        }
    }
}
