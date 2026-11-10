package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.formatCoverageDate
import com.grupo8_uniandes.solventa.domain.bff.issuance.guidanceFor
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import com.grupo8_uniandes.solventa.policy.PolicyDetailUiState
import com.grupo8_uniandes.solventa.policy.PolicyPhase
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography
import java.math.BigDecimal

@Composable
fun PolizaDetalleScreen(
    state: PolicyDetailUiState,
    onExpiryNotices: () -> Unit = {},
    modifier: Modifier = Modifier,
    renewalChecked: Boolean = false,
    renewalMissing: Boolean = false,
    onRenewal: (Boolean) -> Unit = {},
    onOpenClaim: (String) -> Unit = {},
    onReportClaim: () -> Unit = {},
) {
    val detail = state.detail
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
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
            if (state.phase == PolicyPhase.Ready && detail != null) {
                Text(text = detail.ramo, style = MaterialTheme.typography.bodyLarge)
                StatusBadge(policyStatus(detail.estado), "policy_status")
                SectionLabel(stringResource(R.string.policy_vigencia))
                Text(
                    text = vigencia(detail),
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.testTag("policy_vigencia"),
                )
                SectionLabel(stringResource(R.string.policy_coverages))
                if (detail.coberturas.isEmpty()) {
                    Text(text = detail.resumen, style = MaterialTheme.typography.bodyLarge)
                }
                detail.coberturas.forEach { coverage ->
                    Text(
                        text = coverage.nombre,
                        style = MaterialTheme.typography.bodyLarge,
                        modifier = Modifier.testTag("policy_coverage_${coverage.nombre}"),
                    )
                    Text(
                        text = stringResource(
                            R.string.policy_coverage_limit,
                            pesos(coverage.sumaAsegurada, detail.moneda),
                        ),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    if (coverage.deducible != 0.0) {
                        Text(
                            text = stringResource(
                                R.string.policy_deductible,
                                pesos(coverage.deducible, detail.moneda),
                            ),
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.testTag("policy_deductible_${coverage.nombre}"),
                        )
                    }
                }
                if (detail.primaTotal != null) {
                    SectionLabel(stringResource(R.string.policy_annual_premium))
                    Text(
                        text = pesos(detail.primaTotal, detail.moneda),
                        style = SolventaTypography.amount,
                        modifier = Modifier.testTag("policy_prima"),
                    )
                }
                if (detail.renovable) {
                    SectionLabel(stringResource(R.string.policy_renewal_title))
                    RenewalChoice(
                        checked = renewalChecked,
                        helper = stringResource(R.string.renewal_off_issued),
                        missing = renewalMissing,
                        onChecked = onRenewal,
                    )
                }
                val cancelacion = detail.cancelacion
                if (detail.estado.equals("CANCELADA", ignoreCase = true) && cancelacion != null) {
                    SolventaCard(testTag = "policy_cancelacion") {
                        SectionLabel(stringResource(R.string.policy_cancelled))
                        cancelacion.motivo?.takeIf { it.isNotBlank() }?.let { motivo ->
                            Text(text = motivo, style = MaterialTheme.typography.bodyLarge)
                        }
                        cancelacion.canceladaEn?.takeIf { it.isNotBlank() }?.let { fecha ->
                            Text(
                                text = stringResource(R.string.policy_cancel_date, shownDate(fecha)),
                                style = MaterialTheme.typography.bodyMedium,
                            )
                        }
                        cancelacion.devolucionEstimada?.let { devolucion ->
                            Text(
                                text = stringResource(
                                    R.string.policy_refund,
                                    pesos(devolucion, detail.moneda),
                                ),
                                style = SolventaTypography.amount,
                                modifier = Modifier.testTag("policy_refund"),
                            )
                        }
                    }
                }
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
        if (state.phase == PolicyPhase.Ready && detail != null) {
            SectionLabel(stringResource(R.string.policy_claims))
            if (state.claims.isEmpty()) {
                Text(
                    text = stringResource(R.string.policy_claims_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.testTag("policy_claims_empty"),
                )
            }
            state.claims.forEach { claim ->
                ClaimOfPolicy(claim, onOpenClaim)
            }
            SolventaButton(
                text = stringResource(R.string.policy_report_claim),
                style = SolventaButtonStyle.Outlined,
                onClick = onReportClaim,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_report_claim",
            )
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

@Composable
private fun ClaimOfPolicy(claim: ClaimSummary, onOpen: (String) -> Unit) {
    SolventaCard(
        onClick = { onOpen(claim.id) },
        testTag = "policy_claim_${claim.siniestroId}",
    ) {
        Text(text = claim.siniestroId, style = SolventaTypography.amount)
        Text(text = claim.whatHappened(), style = MaterialTheme.typography.bodyLarge)
        Text(text = claim.statusWords(), style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun SectionLabel(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleMedium,
        modifier = Modifier.padding(top = SolventaSpacing.s8),
    )
}

@Composable
private fun StatusBadge(text: String, tag: String) {
    Surface(
        color = MaterialTheme.colorScheme.primaryContainer,
        shape = MaterialTheme.shapes.small,
        modifier = Modifier.testTag(tag),
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.padding(horizontal = SolventaSpacing.s8, vertical = SolventaSpacing.s4),
        )
    }
}

private fun policyStatus(estado: String): String = when (estado.lowercase()) {
    "vigente" -> "Vigente"
    "cancelada" -> "Cancelada"
    "por_vencer" -> "Por vencer"
    else -> estado
}

private fun vigencia(detail: PolicyDetail): String {
    val inicio = detail.inicioVigencia?.takeIf { it.isNotBlank() }
    val fin = (detail.finVigencia ?: detail.venceEn).takeIf { it.isNotBlank() }
    return when {
        inicio != null && fin != null -> "${shownDate(inicio)} – ${shownDate(fin)}"
        fin != null -> shownDate(fin)
        else -> ""
    }
}

private fun shownDate(raw: String): String = runCatching { formatCoverageDate(raw.take(10)) }.getOrDefault(raw)

private fun pesos(amount: Double, moneda: String): String =
    formatPremium(BigDecimal.valueOf(amount), moneda.ifBlank { "COP" }, Region.Colombia)
