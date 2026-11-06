package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.issuance.CardFranchise
import com.grupo8_uniandes.solventa.domain.issuance.CardNumber
import com.grupo8_uniandes.solventa.issuance.CardUiState
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun ConfirmacionTarjetaScreen(
    state: CardUiState,
    onTitular: (String) -> Unit,
    onNumero: (String) -> Unit,
    onMes: (String) -> Unit,
    onAnio: (String) -> Unit,
    onCodigo: (String) -> Unit,
    onConfirm: () -> Unit,
    onBackToOffer: () -> Unit,
    onLeave: () -> Unit,
    modifier: Modifier = Modifier,
) {
    DisposableEffect(Unit) {
        onDispose { onLeave() }
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_confirmacion_tarjeta"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        SolventaCard(outlined = true, testTag = "card_premium") {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = stringResource(R.string.card_premium),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.weight(1f),
                )
                Icon(
                    painter = painterResource(R.drawable.chevron_right),
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(
                text = stringResource(R.string.card_readonly),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                text = stringResource(R.string.card_discard_meta),
                style = SolventaTypography.amount,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
        SolventaTextField(
            value = state.titular,
            onValueChange = onTitular,
            label = stringResource(R.string.card_holder),
            helper = stringResource(R.string.card_holder_hint),
            externalLabel = true,
            placeholder = stringResource(R.string.card_holder_placeholder),
            testTag = "field_titular",
        )
        val numberHint = when (CardNumber.franchise(state.numero)) {
            CardFranchise.Amex -> R.string.card_number_hint_amex
            CardFranchise.Diners -> R.string.card_number_hint_diners
            else -> R.string.card_number_hint
        }
        SolventaTextField(
            value = state.numero,
            onValueChange = onNumero,
            label = stringResource(R.string.card_number),
            helper = stringResource(numberHint),
            externalLabel = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            inputTransformation = CardNumberInput,
            outputTransformation = CardNumberOutput,
            placeholder = stringResource(R.string.card_number_placeholder),
            testTag = "field_tarjeta",
        )
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
        ) {
            SolventaTextField(
                value = state.mes,
                onValueChange = onMes,
                label = stringResource(R.string.card_expiry_month),
                helper = stringResource(R.string.card_expiry_part_hint),
                externalLabel = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.weight(1f),
                placeholder = stringResource(R.string.card_expiry_month_placeholder),
                testTag = "field_mes",
            )
            SolventaTextField(
                value = state.anio,
                onValueChange = onAnio,
                label = stringResource(R.string.card_expiry_year),
                helper = stringResource(R.string.card_expiry_part_hint),
                externalLabel = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.weight(1f),
                placeholder = stringResource(R.string.card_expiry_year_placeholder),
                testTag = "field_anio",
            )
        }
        SolventaTextField(
            value = state.codigo,
            onValueChange = onCodigo,
            label = stringResource(R.string.card_code),
            helper = stringResource(R.string.card_code_hint),
            externalLabel = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            placeholder = stringResource(R.string.card_code_placeholder),
            testTag = "field_codigo",
        )
        SolventaButton(
            text = stringResource(R.string.card_confirm),
            style = SolventaButtonStyle.Filled,
            onClick = onConfirm,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_confirmar_pago",
        )
        SolventaButton(
            text = stringResource(R.string.card_back_offer),
            style = SolventaButtonStyle.Outlined,
            onClick = onBackToOffer,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_volver_oferta",
        )
    }
}
