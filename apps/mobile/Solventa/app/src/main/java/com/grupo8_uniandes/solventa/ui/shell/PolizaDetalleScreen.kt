package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.domain.bff.issuance.detailMeta
import com.grupo8_uniandes.solventa.domain.bff.issuance.guidanceFor
import com.grupo8_uniandes.solventa.domain.bff.issuance.listBody
import com.grupo8_uniandes.solventa.policy.PolicyDetailUiState
import com.grupo8_uniandes.solventa.policy.PolicyPhase
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun PolizaDetalleScreen(
    state: PolicyDetailUiState,
    onExpiryNotices: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val detail = PolicyDetail(state.numero, state.ramo, state.resumen, state.estado, state.venceEn, state.queHacer)
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SolventaSpacing.gutter)
            .testTag("screen_poliza_detalle"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.policy_detail_title),
            style = MaterialTheme.typography.headlineMedium,
        )
        SolventaCard {
            Text(
                text = state.numero,
                style = SolventaTypography.amount,
                modifier = Modifier.testTag("policy_numero"),
            )
            if (state.phase == PolicyPhase.Ready) {
                Text(
                    text = listBody(
                        WalletEntry(state.numero, state.ramo, state.resumen, state.estado, state.venceEn),
                    ),
                    style = MaterialTheme.typography.bodyLarge,
                )
                Text(text = detailMeta(detail), style = SolventaTypography.amount)
                val guidance = guidanceFor(detail)
                if (guidance.isNotEmpty()) {
                    Text(
                        text = guidance,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.testTag("policy_guidance"),
                    )
                }
            }
        }
        if (state.notice) {
            Text(
                text = stringResource(R.string.policy_sync_notice),
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.testTag("policy_sync_notice"),
            )
        }
        SolventaButton(
            text = stringResource(R.string.action_expiry_notices),
            style = SolventaButtonStyle.Text,
            onClick = onExpiryNotices,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_expiry_notices",
        )
    }
}
