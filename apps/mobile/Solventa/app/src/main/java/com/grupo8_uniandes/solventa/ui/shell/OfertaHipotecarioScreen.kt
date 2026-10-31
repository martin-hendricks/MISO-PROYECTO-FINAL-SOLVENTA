package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.mortgage.FirmMortgageOffer
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ShowMortgageOffer
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun OfertaHipotecarioScreen(
    offer: FirmMortgageOffer,
    onAccept: () -> Unit,
    onReviewLater: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val catalogCoverage = stringResource(R.string.mortgage_offer_coverage)
    val coverage = if (offer.coverage == ShowMortgageOffer.DEFAULT_COVERAGE) {
        catalogCoverage
    } else {
        offer.coverage
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_oferta_hipotecario"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        SolventaCard(outlined = true, testTag = "mortgage_offer_card") {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = stringResource(R.string.mortgage_offer_heading),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier
                        .weight(1f)
                        .testTag("mortgage_offer_heading"),
                )
                Icon(
                    painter = painterResource(R.drawable.chevron_right),
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier
                        .size(24.dp)
                        .testTag("mortgage_offer_chevron"),
                )
            }
            Text(
                text = coverage,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.testTag("mortgage_offer_coverage"),
            )
            Text(
                text = stringResource(R.string.mortgage_offer_premium, offer.amountText),
                style = SolventaTypography.amount,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.testTag("mortgage_offer_premium"),
            )
        }
        SolventaButton(
            text = stringResource(R.string.action_accept_offer),
            style = SolventaButtonStyle.Filled,
            onClick = onAccept,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_accept_mortgage",
        )
        SolventaButton(
            text = stringResource(R.string.action_review_later),
            style = SolventaButtonStyle.Outlined,
            onClick = onReviewLater,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_review_later",
        )
    }
}
