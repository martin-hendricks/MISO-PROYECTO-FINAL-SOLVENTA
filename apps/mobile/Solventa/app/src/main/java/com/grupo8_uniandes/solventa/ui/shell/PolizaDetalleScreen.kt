package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun PolizaDetalleScreen(
    policyId: String,
    onSecondary: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var note by rememberSaveable { mutableStateOf("") }
    val fieldValue = stringResource(R.string.field_value)
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SolventaSpacing.gutter)
            .testTag("screen_poliza_detalle"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.policy_detail_title),
            style = MaterialTheme.typography.headlineMedium,
        )
        SolventaCard {
            Text(text = policyId, style = SolventaTypography.amount)
        }
        SolventaTextField(
            value = note.ifEmpty { fieldValue },
            onValueChange = { note = it },
            label = stringResource(R.string.field_label),
            helper = stringResource(R.string.field_helper_error),
            state = SolventaFieldState.Error,
        )
        SolventaButton(
            text = stringResource(R.string.action_view_policy),
            style = SolventaButtonStyle.Filled,
            onClick = {},
        )
        SolventaButton(
            text = stringResource(R.string.action_secondary),
            style = SolventaButtonStyle.Outlined,
            onClick = onSecondary,
        )
    }
}
