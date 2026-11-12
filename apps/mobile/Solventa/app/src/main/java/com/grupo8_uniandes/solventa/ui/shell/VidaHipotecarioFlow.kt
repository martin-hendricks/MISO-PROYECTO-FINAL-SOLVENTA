package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ShowMortgageOffer
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.mortgage.MortgageOfferUi
import com.grupo8_uniandes.solventa.mortgage.MortgageOfferViewModel
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun VidaHipotecarioFlow(
    viewModel: MortgageOfferViewModel,
    region: Region,
    onAccept: (prima: Long, moneda: String) -> Unit,
    onDecline: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    when (val current = state) {
        MortgageOfferUi.Consent -> ConsentimientoHipotecarioStep(
            onAuthorize = viewModel::authorize,
            onDecline = onDecline,
            modifier = modifier,
        )
        MortgageOfferUi.Requesting -> FlowMessage(
            text = stringResource(R.string.mortgage_profiling_requesting),
            testTag = "mortgage_offer_requesting",
            modifier = modifier,
        )
        MortgageOfferUi.Unavailable -> FlowMessage(
            text = stringResource(R.string.mortgage_offer_unavailable),
            testTag = "mortgage_offer_unavailable",
            modifier = modifier,
        ) {
            SolventaButton(
                text = stringResource(R.string.mortgage_offer_retry),
                style = SolventaButtonStyle.Filled,
                onClick = viewModel::authorize,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_retry_mortgage",
            )
            SolventaButton(
                text = stringResource(R.string.action_review_later),
                style = SolventaButtonStyle.Outlined,
                onClick = onDecline,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_review_later",
            )
        }
        is MortgageOfferUi.Offer -> {
            val quote = current.quote
            val offer = remember(quote, region) {
                ShowMortgageOffer(region).show(prima = quote.prima, moneda = quote.moneda)
            }
            OfertaHipotecarioScreen(
                offer = offer,
                onAccept = { onAccept(quote.prima, quote.moneda) },
                onReviewLater = onDecline,
                modifier = modifier,
                factores = quote.factores,
                degradada = quote.degradada,
            )
        }
    }
}

@Composable
private fun ConsentimientoHipotecarioStep(
    onAuthorize: () -> Unit,
    onDecline: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_consentimiento_hipotecario"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.mortgage_consent_heading),
            style = MaterialTheme.typography.titleMedium,
        )
        SolventaCard(outlined = true, testTag = "mortgage_consent_card") {
            Text(
                text = stringResource(R.string.mortgage_consent_body),
                style = MaterialTheme.typography.bodyMedium,
            )
            Text(
                text = stringResource(R.string.mortgage_consent_sources),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        SolventaButton(
            text = stringResource(R.string.mortgage_consent_authorize),
            style = SolventaButtonStyle.Filled,
            onClick = onAuthorize,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_authorize_profiling",
        )
        SolventaButton(
            text = stringResource(R.string.mortgage_consent_decline),
            style = SolventaButtonStyle.Outlined,
            onClick = onDecline,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_decline_profiling",
        )
    }
}

@Composable
private fun FlowMessage(
    text: String,
    testTag: String,
    modifier: Modifier = Modifier,
    actions: @Composable () -> Unit = {},
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier
                .semantics { liveRegion = LiveRegionMode.Polite }
                .testTag(testTag),
        )
        actions()
    }
}
