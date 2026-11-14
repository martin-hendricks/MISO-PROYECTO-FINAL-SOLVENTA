package com.grupo8_uniandes.solventa.ui.shell

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SelectableDates
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticeProblems
import com.grupo8_uniandes.solventa.domain.bff.claim.canReportClaim
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import com.grupo8_uniandes.solventa.domain.bff.issuance.formatCoverageDate
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaSelect
import com.grupo8_uniandes.solventa.ui.components.SolventaSelectAppearance
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset
import java.util.Locale

object AvisoChrome {
    var titleRes by mutableIntStateOf(R.string.claim_evidence_title)
    var coverTabs by mutableStateOf(false)

    fun reset() {
        titleRes = R.string.claim_evidence_title
        coverTabs = false
    }
}

@Composable
fun AvisoSiniestroScreen(
    onContinue: () -> Unit,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier,
    sentences: List<String>? = null,
    problems: NoticeProblems = NoticeProblems(),
    policies: List<PolicyEntry> = emptyList(),
    policiesLoaded: Boolean = false,
    geotag: Boolean = false,
    geo: GeoPoint? = null,
    locationDenied: Boolean = false,
    locating: Boolean = false,
    onRevise: ((String, String, String, String) -> Unit)? = null,
    onToggleGeotag: (Boolean) -> Unit = {},
    onUseLocation: () -> Unit = {},
    onLocationDenied: () -> Unit = {},
) {
    val scroll = rememberScrollState()
    val focusManager = LocalFocusManager.current
    LaunchedEffect(scroll) {
        snapshotFlow { scroll.isScrollInProgress }.collect { moving ->
            if (moving) focusManager.clearFocus()
        }
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .imePadding()
            .verticalScroll(scroll)
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_aviso_siniestro"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        val policy = sentences?.getOrNull(0).orEmpty()
        val date = sentences?.getOrNull(1).orEmpty()
        val description = sentences?.getOrNull(2).orEmpty()
        val place = sentences?.getOrNull(3).orEmpty()
        val editable = onRevise != null
        fun revise(nextPolicy: String, nextDate: String, nextDescription: String, nextPlace: String) {
            onRevise?.invoke(nextPolicy, nextDate, nextDescription, nextPlace)
        }
        val selectable = policies.filter { it.canReportClaim() }
        val showNoPolicy = problems.noPolicy || (editable && policiesLoaded && selectable.isEmpty())
        if (showNoPolicy) {
            Text(
                text = stringResource(R.string.claim_no_policy),
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.testTag("claim_no_policy"),
            )
        }
        if (editable && policiesLoaded && selectable.isNotEmpty()) {
            PolicyMenu(
                policies = selectable,
                policy = policy,
                problem = problems.policy,
                onSelect = { revise(it, date, description, place) },
            )
            selectable.firstOrNull { it.numero == policy }?.let { selected ->
                Text(
                    text = noticeExplanation(selected.ramo),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.testTag("claim_notice_explanation"),
                )
            }
        } else if (!showNoPolicy) {
            SolventaTextField(
                value = policy,
                onValueChange = { revise(it, date, description, place) },
                label = stringResource(R.string.claim_notice_policy_label),
                helper = if (problems.policy) {
                    stringResource(R.string.claim_error_policy)
                } else {
                    stringResource(R.string.claim_notice_policy_help)
                },
                state = when {
                    problems.policy -> SolventaFieldState.Error
                    editable -> SolventaFieldState.Default
                    else -> SolventaFieldState.ReadOnly
                },
                externalLabel = true,
                placeholder = stringResource(R.string.claim_notice_policy_hint),
                testTag = "claim_policy",
            )
        }
        ClaimDateField(
            isoDate = date,
            problem = problems.date,
            editable = editable,
            onDate = { revise(policy, it, description, place) },
        )
        SolventaTextField(
            value = description,
            onValueChange = { revise(policy, date, it, place) },
            label = stringResource(R.string.claim_notice_description_label),
            helper = if (problems.description) stringResource(R.string.claim_error_description) else "",
            placeholder = stringResource(R.string.claim_notice_description_hint),
            state = when {
                problems.description -> SolventaFieldState.Error
                editable -> SolventaFieldState.Default
                else -> SolventaFieldState.ReadOnly
            },
            externalLabel = true,
            testTag = "claim_description",
        )
        SolventaTextField(
            value = place,
            onValueChange = { revise(policy, date, description, it) },
            label = stringResource(R.string.claim_notice_place_label),
            helper = if (problems.place) stringResource(R.string.claim_error_place) else stringResource(R.string.claim_notice_place_help),
            placeholder = stringResource(R.string.claim_notice_place_hint),
            state = when {
                problems.place -> SolventaFieldState.Error
                editable -> SolventaFieldState.Default
                else -> SolventaFieldState.ReadOnly
            },
            externalLabel = true,
            testTag = "claim_place",
        )
        GeotagBlock(
            geotag = geotag,
            geo = geo,
            locationDenied = locationDenied,
            locating = locating,
            onToggleGeotag = onToggleGeotag,
            onUseLocation = onUseLocation,
            onLocationDenied = onLocationDenied,
        )
        val policySelected = selectable.any { it.numero == policy }
        val waitingForMap = geotag && locating && geo == null
        SolventaButton(
            text = stringResource(R.string.claim_notice_continue),
            style = SolventaButtonStyle.Filled,
            onClick = onContinue,
            enabled = (!editable || !policiesLoaded || policySelected) && !waitingForMap,
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_continue",
        )
        SolventaButton(
            text = stringResource(R.string.claim_notice_cancel),
            style = SolventaButtonStyle.Outlined,
            onClick = onCancel,
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_cancel",
        )
    }
}

@Composable
private fun PolicyMenu(
    policies: List<PolicyEntry>,
    policy: String,
    problem: Boolean,
    onSelect: (String) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val labels = policies.map { "${it.numero} · ${it.ramo}" }
    val current = labels.firstOrNull { it.substringBefore(" · ") == policy }.orEmpty()
    SolventaSelect(
        label = stringResource(R.string.claim_notice_policy_label),
        value = current,
        options = labels,
        expanded = expanded,
        onExpandedChange = { expanded = it },
        onSelect = { chosen -> onSelect(chosen.substringBefore(" · ")) },
        appearance = SolventaSelectAppearance.Field,
        optionTag = { label -> "claim_policy_option_${label.substringBefore(" · ")}" },
        fieldTag = "claim_policy",
        placeholder = stringResource(R.string.claim_notice_policy_hint),
    )
    Text(
        text = if (problem) {
            stringResource(R.string.claim_error_policy)
        } else {
            stringResource(R.string.claim_notice_policy_help)
        },
        style = MaterialTheme.typography.bodySmall,
        color = if (problem) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = if (problem) Modifier.testTag("claim_policy_error") else Modifier,
    )
}

@Composable
private fun GeotagBlock(
    geotag: Boolean,
    geo: GeoPoint?,
    locationDenied: Boolean,
    locating: Boolean,
    onToggleGeotag: (Boolean) -> Unit,
    onUseLocation: () -> Unit,
    onLocationDenied: () -> Unit,
) {
    val context = LocalContext.current
    val requestLocation = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (granted) onUseLocation() else onLocationDenied()
    }
    fun requestOrLocate() {
        val granted = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION,
        ) == PackageManager.PERMISSION_GRANTED
        if (granted) onUseLocation() else requestLocation.launch(Manifest.permission.ACCESS_FINE_LOCATION)
    }
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            text = stringResource(R.string.claim_geotag),
            style = MaterialTheme.typography.bodyLarge,
        )
        Switch(
            checked = geotag,
            onCheckedChange = { enabled ->
                onToggleGeotag(enabled)
                if (enabled) requestOrLocate()
            },
            modifier = Modifier.testTag("claim_geotag"),
        )
    }
    if (geotag && locating && geo == null) {
        Text(
            text = stringResource(R.string.claim_locating),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.testTag("claim_locating"),
        )
    }
    geo?.let { point ->
        Text(
            text = point.line(),
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.testTag("claim_geo_line"),
        )
        if (showClaimMap()) {
            ClaimLocationMap(
                point = point,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(180.dp)
                    .testTag("claim_geo_map"),
            )
        }
    }
    if (locationDenied) {
        Text(
            text = stringResource(R.string.claim_geo_denied),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.error,
        )
        Text(
            text = stringResource(R.string.claim_geo_denied_help),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
    }
}

private fun GeoPoint.line(): String =
    "GPS ${"%.4f".format(Locale.US, lat)}, ${"%.4f".format(Locale.US, lng)} · ±$precisionM m"

@Composable
private fun ClaimDateField(
    isoDate: String,
    problem: Boolean,
    editable: Boolean,
    onDate: (String) -> Unit,
) {
    var open by remember { mutableStateOf(false) }
    val shown = if (isoDate.isBlank()) "" else runCatching { formatCoverageDate(isoDate) }.getOrDefault(isoDate)
    val hint = stringResource(R.string.claim_notice_date_hint)
    val shape = RoundedCornerShape(8.dp)
    Column(Modifier.fillMaxWidth()) {
        Text(
            text = stringResource(R.string.claim_notice_date_label),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(SolventaSpacing.s4))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(SolventaSpacing.minTouch)
                .clip(shape)
                .background(MaterialTheme.colorScheme.surfaceContainerLowest)
                .border(
                    1.dp,
                    if (problem) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.outlineVariant,
                    shape,
                )
                .clickable(enabled = editable) { open = true }
                .testTag("claim_date")
                .padding(horizontal = SolventaSpacing.s12),
            contentAlignment = Alignment.CenterStart,
        ) {
            Text(
                text = shown.ifBlank { hint },
                style = SolventaTypography.amount,
                color = if (shown.isBlank()) {
                    MaterialTheme.colorScheme.onSurfaceVariant
                } else {
                    MaterialTheme.colorScheme.onSurface
                },
            )
        }
        if (problem) {
            Spacer(Modifier.height(SolventaSpacing.s4))
            Text(
                text = stringResource(R.string.claim_error_date),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
            )
        }
    }
    if (open) {
        val initial = isoToUtcMillis(isoDate) ?: isoToUtcMillis(LocalDate.now(ZoneOffset.UTC).toString())
        val state = rememberDatePickerState(
            initialSelectedDateMillis = initial,
            selectableDates = ClaimDates,
        )
        DatePickerDialog(
            onDismissRequest = { open = false },
            confirmButton = {
                TextButton(
                    onClick = {
                        state.selectedDateMillis?.let { onDate(utcMillisToIso(it)) }
                        open = false
                    },
                ) { Text(stringResource(R.string.claim_date_confirm)) }
            },
            dismissButton = {
                TextButton(onClick = { open = false }) {
                    Text(stringResource(R.string.claim_notice_cancel))
                }
            },
        ) {
            DatePicker(state = state)
        }
    }
}

private object ClaimDates : SelectableDates {
    override fun isSelectableDate(utcTimeMillis: Long): Boolean {
        val day = Instant.ofEpochMilli(utcTimeMillis).atZone(ZoneOffset.UTC).toLocalDate()
        return !day.isAfter(LocalDate.now(ZoneOffset.UTC))
    }
}

private fun isoToUtcMillis(iso: String): Long? = runCatching {
    LocalDate.parse(iso).atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli()
}.getOrNull()

private fun utcMillisToIso(millis: Long): String =
    Instant.ofEpochMilli(millis).atZone(ZoneOffset.UTC).toLocalDate().toString()

@Composable
private fun noticeExplanation(ramo: String): String = when (ramo) {
    "Protección de dispositivo" -> stringResource(R.string.claim_notice_device)
    "SOAT motocicleta" -> stringResource(R.string.claim_notice_soat)
    "Microseguro de vida", "Vida hipotecario", "Vida crediticia" -> stringResource(R.string.claim_notice_life)
    "Clima y vuelos" -> stringResource(R.string.claim_notice_climate)
    else -> stringResource(R.string.claim_notice_ramo, ramo)
}
