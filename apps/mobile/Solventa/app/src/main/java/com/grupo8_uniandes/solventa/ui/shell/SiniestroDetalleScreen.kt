package com.grupo8_uniandes.solventa.ui.shell

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimDetail
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimEvidence
import com.grupo8_uniandes.solventa.domain.bff.issuance.formatCoverageDate
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography
import java.math.BigDecimal

@Composable
fun SiniestroDetalleScreen(
    claimId: String,
    modifier: Modifier = Modifier,
    claim: ClaimDetail? = null,
    missing: Boolean = false,
    failed: Boolean = false,
    onRetry: () -> Unit = {},
    onOpenPolicy: (String) -> Unit = {},
    onOpenEvidence: (String) -> Unit = {},
    onOpenWallet: () -> Unit = {},
    onOpenProviders: () -> Unit = {},
    region: Region = Region.Colombia,
    loadThumb: suspend (String) -> Bitmap? = { null },
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_siniestro_detalle"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        val summary = claim?.summary
        Text(
            text = stringResource(R.string.destination_siniestros),
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.semantics { heading() },
        )
        Text(
            text = summary?.siniestroId ?: claimId,
            style = SolventaTypography.amount,
            modifier = Modifier.testTag("claim_detail_title"),
        )
        if (summary != null) {
            Text(text = summary.ramo, style = MaterialTheme.typography.bodyLarge)
            SolventaButton(
                text = stringResource(R.string.action_providers),
                style = SolventaButtonStyle.Outlined,
                onClick = onOpenProviders,
                testTag = "action_open_providers",
            )
            Surface(
                color = MaterialTheme.colorScheme.primaryContainer,
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.testTag("claim_status"),
            ) {
                Text(
                    text = summary.statusWords(),
                    style = MaterialTheme.typography.labelLarge,
                    modifier = Modifier.padding(horizontal = SolventaSpacing.s8, vertical = SolventaSpacing.s4),
                )
            }
        }
        claim?.motivo?.takeIf { it.isNotBlank() && summary?.resultado == "rechazado" }?.let { motivo ->
            Text(
                text = stringResource(R.string.claim_reject_reason, motivo),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("claim_reject_reason"),
            )
        }
        if (claim != null && summary != null) {
            SolventaCard(testTag = "claim_facts") {
                claim.poliza?.takeIf { it.isNotBlank() }?.let { poliza ->
                    Fact(stringResource(R.string.claim_policy), poliza, "claim_policy") {
                        onOpenPolicy(poliza)
                    }
                }
                summary.fecha?.takeIf { it.isNotBlank() }?.let { fecha ->
                    Fact(stringResource(R.string.claim_event_date), shownDate(fecha), "claim_fecha")
                }
                claim.descripcion?.takeIf { it.isNotBlank() }?.let { texto ->
                    Fact(stringResource(R.string.claim_description), texto, "claim_descripcion")
                }
                claim.lugar?.takeIf { it.isNotBlank() }?.let { lugar ->
                    Fact(stringResource(R.string.claim_place), lugar, "claim_lugar")
                }
                val ubicacion = claim.geo?.let { "${it.lat}, ${it.lng}" }
                    ?: stringResource(R.string.claim_no_geo)
                Fact(stringResource(R.string.claim_location), ubicacion, "claim_ubicacion")
                summary.reserva?.let { reserva ->
                    Fact(
                        stringResource(R.string.claim_reserve),
                        pesos(reserva, summary.moneda ?: "COP", region),
                        "claim_reserva",
                    )
                }
            }
            claim.pago?.let { pago ->
                SolventaCard(testTag = "claim_pago") {
                    Text(
                        text = stringResource(R.string.claim_payment),
                        style = MaterialTheme.typography.titleMedium,
                    )
                    Text(
                        text = pesos(pago.monto, pago.moneda, region),
                        style = SolventaTypography.amount,
                    )
                    if (pago.comprobante.isNotBlank()) {
                        Text(text = pago.comprobante, style = MaterialTheme.typography.bodyMedium)
                    }
                    if (pago.fecha.isNotBlank()) {
                        Text(text = shownDate(pago.fecha), style = MaterialTheme.typography.bodyMedium)
                    }
                    SolventaButton(
                        text = stringResource(R.string.billetera_ver_en),
                        style = SolventaButtonStyle.Outlined,
                        onClick = onOpenWallet,
                        testTag = "claim_ver_billetera",
                    )
                }
            }
            Text(
                text = stringResource(R.string.claim_evidence),
                style = MaterialTheme.typography.titleMedium,
            )
            if (claim.evidencia.isEmpty()) {
                Text(
                    text = stringResource(R.string.claim_no_evidence),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.testTag("claim_no_evidence"),
                )
            }
            claim.evidencia.forEach { item ->
                EvidenceItem(item, onOpenEvidence, loadThumb)
            }
            Text(
                text = stringResource(R.string.claim_history),
                style = MaterialTheme.typography.titleMedium,
            )
            claim.historial.forEach { step ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("claim_history_${step.estado}"),
                    horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .testTag("claim_history_mark"),
                    )
                    Column {
                        Text(
                            text = step.estadoTexto.ifBlank { step.estado },
                            style = MaterialTheme.typography.bodyLarge,
                        )
                        if (step.fecha.isNotBlank()) {
                            Text(
                                text = shownDate(step.fecha),
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }
        }
        if (missing) {
            Text(
                text = stringResource(R.string.claim_not_found),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("claim_not_found"),
            )
        }
        if (failed) {
            Text(
                text = stringResource(R.string.load_failed),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("claim_detail_failed"),
            )
            SolventaButton(
                text = stringResource(R.string.claim_retry),
                style = SolventaButtonStyle.Outlined,
                onClick = onRetry,
                testTag = "claim_detail_retry",
            )
        }
    }
}

@Composable
private fun Fact(label: String, value: String, tag: String, onClick: (() -> Unit)? = null) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onClick == null) Modifier else Modifier.clickable(onClick = onClick))
            .testTag(tag),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(text = value, style = MaterialTheme.typography.bodyLarge)
    }
}

@Composable
private fun EvidenceItem(
    item: ClaimEvidence,
    onOpen: (String) -> Unit,
    loadThumb: suspend (String) -> Bitmap?,
) {
    val image = item.contentType.startsWith("image/") || item.tipo.equals("foto", ignoreCase = true)
    val remote = image && (item.url.startsWith("http://") || item.url.startsWith("https://"))
    var thumb by remember(item.url) { mutableStateOf<Bitmap?>(null) }
    var settled by remember(item.url) { mutableStateOf(!remote) }
    if (remote) {
        LaunchedEffect(item.url) {
            thumb = loadThumb(item.url)
            settled = true
        }
    }
    val open = { if (item.url.isNotBlank()) onOpen(item.url) }
    val label = evidenceLabel(item)
    if (image) {
        Surface(
            color = MaterialTheme.colorScheme.surfaceContainerHigh,
            shape = MaterialTheme.shapes.medium,
            modifier = Modifier
                .size(96.dp)
                .clickable(onClick = open)
                .testTag("claim_evidence_${item.nombre}"),
        ) {
            val bitmap = thumb
            when {
                bitmap != null -> Image(
                    bitmap = bitmap.asImageBitmap(),
                    contentDescription = label,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize(),
                )
                !settled -> Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                    CircularProgressIndicator(
                        modifier = Modifier
                            .size(24.dp)
                            .testTag("claim_evidence_loading_${item.nombre}"),
                        strokeWidth = 2.dp,
                    )
                }
                else -> Box(contentAlignment = Alignment.Center, modifier = Modifier.padding(SolventaSpacing.s8)) {
                    Text(text = label, style = MaterialTheme.typography.labelLarge)
                }
            }
        }
    } else {
        Text(
            text = item.nombre,
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier
                .clickable(onClick = open)
                .testTag("claim_evidence_${item.nombre}"),
        )
    }
}

private fun evidenceLabel(item: ClaimEvidence): String {
    val raw = item.nombre.ifBlank { item.url }
    return raw.substringBefore('?').substringAfterLast('/').ifBlank { raw }
}

private fun shownDate(raw: String): String = runCatching { formatCoverageDate(raw.take(10)) }.getOrDefault(raw)

private fun pesos(amount: Double, moneda: String, region: Region): String =
    formatPremium(BigDecimal.valueOf(amount), moneda.ifBlank { "COP" }, region)
