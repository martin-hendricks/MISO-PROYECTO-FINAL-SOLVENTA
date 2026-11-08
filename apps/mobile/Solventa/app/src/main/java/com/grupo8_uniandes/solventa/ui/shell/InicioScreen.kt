package com.grupo8_uniandes.solventa.ui.shell

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
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
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.HankenGrotesk
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun InicioScreen(
    state: HomeUiState,
    onNewQuote: () -> Unit,
    onOpenOffer: (String) -> Unit = {},
    onAcceptOffer: (String) -> Unit = {},
    onOpenPolicy: (String) -> Unit = {},
    onOpenClaim: (String) -> Unit = {},
    onOpenMortgage: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val panel = state.panel
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .padding(bottom = SolventaSpacing.s64)
            .testTag("screen_inicio"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s24),
    ) {
        if (state.failed) {
            Text(
                text = stringResource(R.string.load_failed),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier
                    .testTag("load_failed")
                    .semantics { liveRegion = LiveRegionMode.Polite },
            )
        }
        panel.offerId?.let { offerId ->
            HomeSection {
                HomeSectionLabel(R.string.home_section_offer)
                SolventaCard(onClick = { onOpenOffer(offerId) }, testTag = "home_offer") {
                    Column(verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12)) {
                        LabeledValue(
                            label = R.string.home_offer_id,
                            value = offerId,
                            valueStyle = SolventaTypography.amount,
                            testTag = "home_offer_id",
                        )
                        panel.offerRamo?.let { ramo ->
                            LabeledValue(
                                label = R.string.home_offer_ramo,
                                value = ramo,
                                valueStyle = MaterialTheme.typography.bodyLarge,
                                testTag = "home_offer_ramo",
                            )
                        }
                    }
                }
                SolventaButton(
                    text = stringResource(R.string.action_accept_offer),
                    style = SolventaButtonStyle.Filled,
                    onClick = { onAcceptOffer(offerId) },
                    modifier = Modifier.fillMaxWidth(),
                    testTag = "action_accept_offer",
                )
            }
        }
        panel.policyId?.let { policyId ->
            HomeSection {
                HomeSectionLabel(R.string.home_section_policies)
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
        }
        panel.claimId?.let { claimId ->
            HomeSection {
                HomeSectionLabel(R.string.home_section_claims)
                SolventaCard(
                    onClick = { onOpenClaim(claimId) },
                    testTag = "home_claim",
                ) {
                    Text(text = claimId, style = SolventaTypography.amount)
                }
            }
        }
        if (panel.vidaCrediticia) {
            HomeSection {
                HomeSectionLabel(R.string.home_section_mortgage)
                SolventaCard(
                    onClick = onOpenMortgage,
                    testTag = "home_vida_crediticia",
                ) {
                    Text(
                        text = stringResource(R.string.home_vida_crediticia),
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
            }
        }
        HomeSection {
            HomeSectionLabel(R.string.home_section_quote)
            SolventaButton(
                text = stringResource(R.string.action_new_quote),
                style = if (panel.offerId == null) {
                    SolventaButtonStyle.Filled
                } else {
                    SolventaButtonStyle.Outlined
                },
                onClick = onNewQuote,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_new_quote",
            )
        }
    }
}

@Composable
private fun LabeledValue(
    @StringRes label: Int,
    value: String,
    valueStyle: TextStyle,
    testTag: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s4)) {
        Text(
            text = stringResource(label),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = value,
            style = valueStyle,
            modifier = Modifier.testTag(testTag),
        )
    }
}

@Composable
private fun HomeSection(content: @Composable ColumnScope.() -> Unit) {
    Column(
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
        content = content,
    )
}

@Composable
private fun HomeSectionLabel(@StringRes label: Int) {
    Text(
        text = stringResource(label).uppercase(),
        style = sectionLabel,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

private val sectionLabel = TextStyle(
    fontFamily = HankenGrotesk,
    fontWeight = FontWeight.Medium,
    fontSize = 12.sp,
    lineHeight = 16.sp,
    letterSpacing = 0.6.sp,
)
