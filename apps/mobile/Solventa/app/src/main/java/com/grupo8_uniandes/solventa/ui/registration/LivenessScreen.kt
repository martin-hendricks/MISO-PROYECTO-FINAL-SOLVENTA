package com.grupo8_uniandes.solventa.ui.registration

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaSelect
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun LivenessScreen(
    state: LivenessUiState,
    onGivenName: (String) -> Unit,
    onSurnames: (String) -> Unit,
    onEmail: (String) -> Unit,
    onDocumentType: (String) -> Unit,
    onDocumentNumber: (String) -> Unit,
    onPassword: (String) -> Unit,
    onContinue: () -> Unit,
    onExistingAccount: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var typeExpanded by remember { mutableStateOf(false) }
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface)
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_prueba_de_vida"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.onboarding_wordmark),
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Text(
            text = stringResource(R.string.liveness_step),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = stringResource(R.string.liveness_title),
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
        Text(
            text = stringResource(R.string.liveness_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        SolventaTextField(
            value = state.givenName,
            onValueChange = onGivenName,
            label = stringResource(R.string.onboarding_nombre),
            helper = stringResource(R.string.onboarding_nombre_hint),
            testTag = "field_liveness_nombre",
        )
        SolventaTextField(
            value = state.surnames,
            onValueChange = onSurnames,
            label = stringResource(R.string.onboarding_apellidos),
            helper = "",
            testTag = "field_liveness_apellidos",
        )
        SolventaTextField(
            value = state.email,
            onValueChange = onEmail,
            label = stringResource(R.string.onboarding_correo),
            helper = stringResource(R.string.onboarding_correo_hint),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            testTag = "field_liveness_correo",
        )
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s4),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            SolventaSelect(
                label = stringResource(R.string.onboarding_tipo),
                value = state.documentType,
                options = state.documentTypeOptions,
                expanded = typeExpanded,
                onExpandedChange = { typeExpanded = it },
                onSelect = onDocumentType,
            )
            SolventaTextField(
                value = state.documentNumber,
                onValueChange = onDocumentNumber,
                label = stringResource(R.string.onboarding_numero),
                helper = "",
                modifier = Modifier.weight(1f),
                testTag = "field_liveness_numero",
            )
        }
        SolventaTextField(
            value = state.password,
            onValueChange = onPassword,
            label = stringResource(R.string.onboarding_contrasena),
            helper = "",
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            testTag = "field_liveness_contrasena",
        )
        SolventaButton(
            text = stringResource(R.string.action_continuar_onboarding),
            style = SolventaButtonStyle.Filled,
            onClick = onContinue,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_liveness_continuar",
        )
        SolventaButton(
            text = stringResource(R.string.action_ya_tengo_cuenta),
            style = SolventaButtonStyle.Text,
            onClick = onExistingAccount,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_liveness_ya_tengo_cuenta",
        )
    }
}
