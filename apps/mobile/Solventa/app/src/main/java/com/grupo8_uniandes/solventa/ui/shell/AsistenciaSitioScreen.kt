package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.AssistanceForm
import com.grupo8_uniandes.solventa.domain.bff.claim.canReportClaim
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaSelect
import com.grupo8_uniandes.solventa.ui.components.SolventaSelectAppearance
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun AsistenciaSitioScreen(
    form: AssistanceForm,
    onContinue: () -> Unit,
    onCancel: () -> Unit,
    onPolicy: (String) -> Unit = {},
    onDate: (String) -> Unit = {},
    onDescription: (String) -> Unit = {},
    onPlace: (String) -> Unit = {},
    policies: List<PolicyEntry> = emptyList(),
    policiesLoaded: Boolean = false,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .imePadding()
            .testTag("screen_asistencia_sitio"),
    ) {
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
        ) {
            Text(
                text = stringResource(R.string.assistance_registered),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            AssistancePolicyField(
                policyValue = form.policyValue,
                policies = policies,
                policiesLoaded = policiesLoaded,
                onPolicy = onPolicy,
            )
            SolventaTextField(
                value = form.dateValue,
                onValueChange = onDate,
                label = stringResource(R.string.assistance_date_label),
                helper = "",
                state = SolventaFieldState.Default,
                externalLabel = true,
                testTag = "field_fecha",
            )
            SolventaTextField(
                value = form.descriptionValue,
                onValueChange = onDescription,
                label = stringResource(R.string.assistance_description_label),
                helper = "",
                state = SolventaFieldState.Default,
                externalLabel = true,
                testTag = "field_descripcion",
            )
            SolventaTextField(
                value = form.placeValue,
                onValueChange = onPlace,
                label = stringResource(R.string.assistance_place_label),
                helper = stringResource(R.string.assistance_place_help),
                state = SolventaFieldState.Default,
                externalLabel = true,
                testTag = "field_lugar",
            )
        }
        val noPolicy = policiesLoaded && policies.none { it.canReportClaim() }
        Column(
            modifier = Modifier.padding(
                horizontal = SolventaSpacing.gutter,
                vertical = SolventaSpacing.s12,
            ),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
        ) {
            SolventaButton(
                text = stringResource(R.string.assistance_continue),
                style = SolventaButtonStyle.Filled,
                onClick = onContinue,
                enabled = !noPolicy,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_continuar_evidencia",
            )
            SolventaButton(
                text = stringResource(R.string.action_secondary),
                style = SolventaButtonStyle.Outlined,
                onClick = onCancel,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_cancelar_asistencia",
            )
        }
    }
}

@Composable
private fun AssistancePolicyField(
    policyValue: String,
    policies: List<PolicyEntry>,
    policiesLoaded: Boolean,
    onPolicy: (String) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val inForce = policies.filter { it.canReportClaim() }
    if (policiesLoaded && inForce.isEmpty()) {
        Text(
            text = stringResource(R.string.claim_no_policy),
            color = MaterialTheme.colorScheme.error,
            modifier = Modifier.testTag("assistance_no_policy"),
        )
        return
    }
    if (!policiesLoaded && inForce.isEmpty()) {
        SolventaTextField(
            value = policyValue,
            onValueChange = {},
            label = stringResource(R.string.assistance_policy_label),
            helper = stringResource(R.string.assistance_policy_help),
            state = SolventaFieldState.ReadOnly,
            externalLabel = true,
            testTag = "field_poliza",
        )
        return
    }
    val labels = inForce.map { "${it.numero} · ${it.ramo}" }
    val current = labels.firstOrNull { it.substringBefore(" · ") == policyValue.substringBefore(" · ") }.orEmpty()
    SolventaSelect(
        label = stringResource(R.string.assistance_policy_label),
        value = current,
        options = labels,
        expanded = expanded,
        onExpandedChange = { expanded = it },
        onSelect = { chosen -> onPolicy(chosen.substringBefore(" · ")) },
        appearance = SolventaSelectAppearance.Field,
        optionTag = { label -> "assistance_policy_option_${label.substringBefore(" · ")}" },
        fieldTag = "field_poliza",
        placeholder = stringResource(R.string.claim_notice_policy_hint),
    )
    Text(
        text = stringResource(R.string.assistance_policy_help),
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}
