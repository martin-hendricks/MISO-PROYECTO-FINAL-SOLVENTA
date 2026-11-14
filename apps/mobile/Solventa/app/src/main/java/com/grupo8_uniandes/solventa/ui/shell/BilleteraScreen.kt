package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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
import com.grupo8_uniandes.solventa.billetera.BilleteraUiState
import com.grupo8_uniandes.solventa.billetera.WalletPhase
import com.grupo8_uniandes.solventa.domain.bff.billetera.Deposit
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositType
import com.grupo8_uniandes.solventa.domain.bff.billetera.WalletNotice
import com.grupo8_uniandes.solventa.domain.bff.issuance.formatCoverageDate
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import com.grupo8_uniandes.solventa.ui.components.SolventaBanner
import com.grupo8_uniandes.solventa.ui.components.SolventaBannerStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaChip
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun BilleteraScreen(
    state: BilleteraUiState,
    onChip: (DepositType?) -> Unit,
    onOpen: (String) -> Unit,
    onRetry: () -> Unit,
    onClaims: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_billetera"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Notice(state.notice, state.savedAt)
        if (state.phase == WalletPhase.Ready || state.phase == WalletPhase.Empty) {
            val wallet = state.wallet
            if (wallet != null) {
                SolventaCard(testTag = "billetera_recibido") {
                    Text(
                        text = formatPremium(wallet.totalRecibido, wallet.moneda, Region.Colombia),
                        style = SolventaTypography.amount,
                        modifier = Modifier.testTag("billetera_total"),
                    )
                    Text(
                        text = stringResource(R.string.billetera_count, wallet.movimientos.size),
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.testTag("billetera_count"),
                    )
                    Text(
                        text = stringResource(R.string.billetera_recibido),
                        style = MaterialTheme.typography.labelLarge,
                    )
                }
            }
            if (state.phase == WalletPhase.Ready) {
                Chips(state.chip, onChip)
                state.visible.forEach { deposit ->
                    DepositCard(deposit, onOpen)
                }
            }
            if (state.phase == WalletPhase.Empty) {
                Text(text = stringResource(R.string.billetera_empty), modifier = Modifier.testTag("billetera_empty"))
                SolventaButton(
                    text = stringResource(R.string.billetera_ver_siniestros),
                    style = SolventaButtonStyle.Outlined,
                    onClick = onClaims,
                    modifier = Modifier.fillMaxWidth(),
                    testTag = "billetera_ver_siniestros",
                )
            }
            SolventaBanner(
                message = stringResource(R.string.billetera_info),
                style = SolventaBannerStyle.Info,
                modifier = Modifier.testTag("billetera_info"),
            )
        }
        if (state.phase == WalletPhase.Error || state.phase == WalletPhase.FirstLoad) {
            Text(
                text = stringResource(
                    if (state.phase == WalletPhase.FirstLoad) R.string.billetera_first else R.string.billetera_error,
                ),
                modifier = Modifier.testTag("billetera_error"),
            )
            SolventaButton(
                text = stringResource(R.string.billetera_reintentar),
                style = SolventaButtonStyle.Filled,
                onClick = onRetry,
                testTag = "billetera_reintentar",
            )
        }
    }
}

private fun shownWhen(raw: String): String =
    runCatching { formatCoverageDate(raw.take(10)) }.getOrDefault(raw)

@Composable
private fun Notice(notice: WalletNotice, savedAt: String?) {
    val text = when (notice) {
        WalletNotice.Offline -> stringResource(R.string.billetera_offline, savedAt.orEmpty())
        WalletNotice.Updated -> stringResource(R.string.billetera_actualizada)
        else -> return
    }
    Text(text = text, modifier = Modifier.testTag("billetera_notice"))
}

@Composable
private fun Chips(chip: DepositType?, onChip: (DepositType?) -> Unit) {
    Row(
        modifier = Modifier.horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
    ) {
        SolventaChip(stringResource(R.string.billetera_chip_todos), chip == null, { onChip(null) }, testTag = "chip_todos", showSelectionIcon = false)
        SolventaChip(stringResource(R.string.billetera_chip_asistido), chip == DepositType.Assisted, { onChip(DepositType.Assisted) }, testTag = "chip_asistido", showSelectionIcon = false)
        SolventaChip(stringResource(R.string.billetera_chip_automatico), chip == DepositType.Automatic, { onChip(DepositType.Automatic) }, testTag = "chip_automatico", showSelectionIcon = false)
    }
}

@Composable
private fun DepositCard(deposit: Deposit, onOpen: (String) -> Unit) {
    SolventaCard(onClick = { onOpen(deposit.id) }, outlined = true, testTag = "billetera_fila_${deposit.siniestroId}") {
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(text = deposit.siniestroId, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
            Icon(painter = painterResource(R.drawable.chevron_right), contentDescription = null)
        }
        Text(
            text = "${deposit.ramo} · ${deposit.resumen}",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        val amount = formatPremium(deposit.monto, deposit.moneda, Region.Colombia)
        val tail = if (deposit.tipo == DepositType.Automatic) {
            stringResource(R.string.billetera_depositado)
        } else {
            shownWhen(deposit.depositadoEn)
        }
        Text(
            text = "$amount · $tail",
            style = SolventaTypography.amount,
        )
    }
}
