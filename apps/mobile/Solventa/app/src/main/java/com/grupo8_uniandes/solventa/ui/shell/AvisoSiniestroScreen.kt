package com.grupo8_uniandes.solventa.ui.shell

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.core.content.ContextCompat
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticeProblems
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaSelect
import com.grupo8_uniandes.solventa.ui.components.SolventaSelectAppearance
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
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
    policies: List<WalletEntry> = emptyList(),
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
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_aviso_siniestro"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.claim_notice_explanation),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        val policy = sentences?.getOrNull(0) ?: stringResource(R.string.claim_notice_policy_value)
        val date = sentences?.getOrNull(1) ?: stringResource(R.string.claim_notice_date_value)
        val description = sentences?.getOrNull(2) ?: stringResource(R.string.claim_notice_description_value)
        val place = sentences?.getOrNull(3) ?: stringResource(R.string.claim_notice_place_value)
        val editable = onRevise != null
        fun revise(nextPolicy: String, nextDate: String, nextDescription: String, nextPlace: String) {
            onRevise?.invoke(nextPolicy, nextDate, nextDescription, nextPlace)
        }
        val showNoPolicy = problems.noPolicy || (editable && policiesLoaded && policies.isEmpty())
        if (showNoPolicy) {
            Text(
                text = stringResource(R.string.claim_no_policy),
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.testTag("claim_no_policy"),
            )
        }
        if (editable && policiesLoaded && policies.isNotEmpty()) {
            PolicyMenu(
                policies = policies,
                policy = policy,
                problem = problems.policy,
                onSelect = { revise(it, date, description, place) },
            )
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
                testTag = "claim_policy",
            )
        }
        SolventaTextField(
            value = date,
            onValueChange = { revise(policy, it, description, place) },
            label = stringResource(R.string.claim_notice_date_label),
            helper = if (problems.date) stringResource(R.string.claim_error_date) else "",
            state = when {
                problems.date -> SolventaFieldState.Error
                editable -> SolventaFieldState.Default
                else -> SolventaFieldState.ReadOnly
            },
            externalLabel = true,
            testTag = "claim_date",
        )
        SolventaTextField(
            value = description,
            onValueChange = { revise(policy, date, it, place) },
            label = stringResource(R.string.claim_notice_description_label),
            helper = if (problems.description) stringResource(R.string.claim_error_description) else "",
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
        SolventaButton(
            text = stringResource(R.string.claim_notice_continue),
            style = SolventaButtonStyle.Filled,
            onClick = onContinue,
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
    policies: List<WalletEntry>,
    policy: String,
    problem: Boolean,
    onSelect: (String) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val labels = policies.map { "${it.numero} · ${it.ramo}" }
    val current = labels.firstOrNull { it.substringBefore(" · ") == policy } ?: policy
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
            onCheckedChange = onToggleGeotag,
            modifier = Modifier.testTag("claim_geotag"),
        )
    }
    if (geotag) {
        SolventaButton(
            text = stringResource(R.string.claim_use_location),
            style = SolventaButtonStyle.Outlined,
            onClick = {
                val granted = ContextCompat.checkSelfPermission(
                    context,
                    Manifest.permission.ACCESS_FINE_LOCATION,
                ) == PackageManager.PERMISSION_GRANTED
                if (granted) {
                    onUseLocation()
                } else {
                    requestLocation.launch(Manifest.permission.ACCESS_FINE_LOCATION)
                }
            },
            enabled = !locating,
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_use_location",
        )
    }
    geo?.let { point ->
        Text(
            text = point.line(),
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.testTag("claim_geo_line"),
        )
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

private fun GeoPoint.line(): String =
    "GPS ${"%.4f".format(Locale.US, lat)}, ${"%.4f".format(Locale.US, lng)} · ±$precisionM m"
