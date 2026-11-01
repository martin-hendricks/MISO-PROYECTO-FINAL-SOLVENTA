package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
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
    onDecline: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_ver_oferta"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
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
                SolventaCard(outlined = true, testTag = "offer_price") {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = stringResource(R.string.offer_premium_title, state.premiumText),
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.onSurface,
                            modifier = Modifier
                                .weight(1f)
                                .testTag("offer_premium"),
                        )
                        Icon(
                            painter = painterResource(R.drawable.chevron_right),
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    Text(
                        text = stringResource(R.string.offer_card_body, state.ramo),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Text(
                        text = stringResource(R.string.offer_card_meta, state.endDateText),
                        style = SolventaTypography.amount,
                        color = MaterialTheme.colorScheme.onSurface,
                        modifier = Modifier.testTag("offer_end_date"),
                    )
                }
                SolventaButton(
                    text = stringResource(R.string.action_accept_and_issue),
                    style = SolventaButtonStyle.Filled,
                    onClick = { onAccept(state.cotizacionId) },
                    enabled = state.acceptEnabled,
                    modifier = Modifier.fillMaxWidth(),
                    testTag = "action_accept_offer",
                )
                if (state.expired) {
                    SolventaButton(
                        text = stringResource(R.string.action_quote_again),
                        style = SolventaButtonStyle.Tonal,
                        onClick = onQuoteAgain,
                        modifier = Modifier.fillMaxWidth(),
                        testTag = "action_quote_again",
                    )
                } else {
                    SolventaButton(
                        text = stringResource(R.string.action_not_now),
                        style = SolventaButtonStyle.Outlined,
                        onClick = onDecline,
                        modifier = Modifier.fillMaxWidth(),
                        testTag = "action_not_now",
                    )
                }
            }
        }
    }
}
