package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.AssistanceForm
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun AsistenciaSitioScreen(
    form: AssistanceForm,
    onContinue: () -> Unit,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_asistencia_sitio"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.assistance_registered),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        SolventaTextField(
            value = form.policyValue,
            onValueChange = {},
            label = stringResource(R.string.assistance_policy_label),
            helper = stringResource(R.string.assistance_policy_help),
            state = SolventaFieldState.ReadOnly,
            externalLabel = true,
            testTag = "field_poliza",
        )
        SolventaTextField(
            value = form.dateValue,
            onValueChange = {},
            label = stringResource(R.string.assistance_date_label),
            helper = "",
            state = SolventaFieldState.ReadOnly,
            externalLabel = true,
            testTag = "field_fecha",
        )
        SolventaTextField(
            value = form.descriptionValue,
            onValueChange = {},
            label = stringResource(R.string.assistance_description_label),
            helper = "",
            state = SolventaFieldState.ReadOnly,
            externalLabel = true,
            testTag = "field_descripcion",
        )
        SolventaTextField(
            value = form.placeValue,
            onValueChange = {},
            label = stringResource(R.string.assistance_place_label),
            helper = stringResource(R.string.assistance_place_help),
            state = SolventaFieldState.ReadOnly,
            externalLabel = true,
            testTag = "field_lugar",
        )
        SolventaButton(
            text = stringResource(R.string.assistance_continue),
            style = SolventaButtonStyle.Filled,
            onClick = onContinue,
            testTag = "action_continuar_evidencia",
        )
        SolventaButton(
            text = stringResource(R.string.action_secondary),
            style = SolventaButtonStyle.Outlined,
            onClick = onCancel,
            testTag = "action_cancelar_asistencia",
        )
    }
}
