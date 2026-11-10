package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.billetera.DepositoUiState
import com.grupo8_uniandes.solventa.billetera.DepositPhase
import com.grupo8_uniandes.solventa.domain.bff.billetera.Deposit
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositType
import com.grupo8_uniandes.solventa.domain.bff.billetera.WalletNotice
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaStatus
import com.grupo8_uniandes.solventa.ui.components.SolventaStatusMark
import com.grupo8_uniandes.solventa.ui.theme.HankenGrotesk
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun DepositoScreen(
    state: DepositoUiState,
    onBack: () -> Unit,
    onClaim: () -> Unit,
    onDownload: () -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SolventaSpacing.gutter)
            .testTag("screen_deposito"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        if (state.notice == WalletNotice.Offline) {
            Text(
                text = stringResource(R.string.billetera_offline, state.savedAt.orEmpty()),
                modifier = Modifier.testTag("deposito_notice"),
            )
        }
        if (state.notice == WalletNotice.Updated) {
            Text(text = stringResource(R.string.billetera_actualizada), modifier = Modifier.testTag("deposito_notice"))
        }
        if (state.needsNetwork) {
            Text(text = stringResource(R.string.billetera_need_network), modifier = Modifier.testTag("deposito_need_network"))
        }
        val deposit = state.deposit
        if (state.phase == DepositPhase.Ready && deposit != null) {
            Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                SolventaStatusMark(status = SolventaStatus.Success)
            }
            Text(
                text = stringResource(R.string.billetera_deposito_title),
                color = MaterialTheme.colorScheme.onSurface,
                fontFamily = HankenGrotesk,
                fontWeight = FontWeight.Medium,
                fontSize = 20.sp,
            )
            DepositCard(deposit)
            Text(
                text = if (deposit.tipo == DepositType.Automatic) {
                    stringResource(R.string.billetera_frase_automatico)
                } else {
                    stringResource(R.string.billetera_frase_asistido)
                },
                style = MaterialTheme.typography.bodyMedium,
            )
            SolventaButton(
                text = stringResource(R.string.billetera_volver),
                style = SolventaButtonStyle.Filled,
                onClick = onBack,
                modifier = Modifier.fillMaxWidth(),
                testTag = "deposito_volver",
            )
            SolventaButton(
                text = stringResource(R.string.billetera_descargar),
                style = SolventaButtonStyle.Outlined,
                onClick = onDownload,
                enabled = state.downloadEnabled,
                modifier = Modifier.fillMaxWidth(),
                testTag = "deposito_descargar",
            )
            SolventaButton(
                text = stringResource(R.string.billetera_ver_siniestro),
                style = SolventaButtonStyle.Outlined,
                onClick = onClaim,
                enabled = !state.offline,
                modifier = Modifier.fillMaxWidth(),
                testTag = "deposito_ver_siniestro",
            )
        }
        if (state.phase == DepositPhase.Missing || state.phase == DepositPhase.Error || state.phase == DepositPhase.FirstLoad) {
            Text(
                text = stringResource(
                    if (state.phase == DepositPhase.Missing) R.string.billetera_ausente else R.string.billetera_error,
                ),
            )
            if (state.phase != DepositPhase.Missing) {
                SolventaButton(
                    text = stringResource(R.string.billetera_reintentar),
                    style = SolventaButtonStyle.Filled,
                    onClick = onRetry,
                    testTag = "deposito_reintentar",
                )
            }
        }
    }
}

@Composable
private fun DepositCard(deposit: Deposit) {
    val amount = formatPremium(deposit.monto, deposit.moneda, Region.Colombia)
    val event = listOf(deposit.resumen, deposit.poliza).filter { it.isNotBlank() }.joinToString(" · ")
    SolventaCard(outlined = true, testTag = "deposito_card") {
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = deposit.ramo.ifBlank { deposit.siniestroId },
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.weight(1f),
            )
            Icon(
                painter = painterResource(R.drawable.chevron_right),
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Text(
            text = event,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.testTag("deposito_poliza"),
        )
        Text(
            text = "$amount ${stringResource(R.string.billetera_depositados)} · ${deposit.comprobante}",
            style = SolventaTypography.amount,
            modifier = Modifier.testTag("deposito_monto"),
        )
    }
}
