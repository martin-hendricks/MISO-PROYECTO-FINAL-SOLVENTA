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
import com.grupo8_uniandes.solventa.offer.OfferPhase
import com.grupo8_uniandes.solventa.offer.OfferUiState
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun VerOfertaScreen(
    state: OfferUiState,
    onAccept: (String) -> Unit,
    onQuoteAgain: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SolventaSpacing.gutter)
            .testTag("screen_ver_oferta"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        when (state.phase) {
            OfferPhase.Pending -> Text(
                text = stringResource(R.string.quote_progress),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("offer_pending"),
            )
            OfferPhase.Failed -> Text(
                text = stringResource(R.string.quote_failed),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("offer_failed"),
            )
            OfferPhase.Ready -> {
                if (state.expired) {
                    Text(
                        text = stringResource(R.string.offer_expired),
                        style = MaterialTheme.typography.bodyLarge,
                        modifier = Modifier.testTag("offer_expired"),
                    )
                }
                SolventaCard(testTag = "offer_price") {
                    Text(
                        text = state.premiumText,
                        style = SolventaTypography.amount,
                        modifier = Modifier.testTag("offer_premium"),
                    )
                    Text(
                        text = state.endDateText,
                        style = MaterialTheme.typography.bodyLarge,
                        modifier = Modifier.testTag("offer_end_date"),
                    )
                }
                SolventaButton(
                    text = stringResource(R.string.action_accept_offer),
                    style = SolventaButtonStyle.Filled,
                    onClick = { onAccept(state.cotizacionId) },
                    enabled = state.acceptEnabled,
                    testTag = "action_accept_offer",
                )
                if (state.expired) {
                    SolventaButton(
                        text = stringResource(R.string.action_quote_again),
                        style = SolventaButtonStyle.Tonal,
                        onClick = onQuoteAgain,
                        testTag = "action_quote_again",
                    )
                }
            }
        }
    }
}
