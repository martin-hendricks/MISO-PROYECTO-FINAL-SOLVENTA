package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteField
import com.grupo8_uniandes.solventa.quote.QuoteUiState
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaCard
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun CotizacionScreen(
    state: QuoteUiState,
    onValueChange: (String) -> Unit,
    onBrandChange: (String) -> Unit,
    onAge: (Boolean) -> Unit,
    onCotizar: () -> Unit,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val required = stringResource(R.string.field_required)
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_cotizacion"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        SolventaCard(testTag = "quote_product") {
            Text(
                text = stringResource(R.string.product_locked),
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = stringResource(R.string.product_coverages),
                style = MaterialTheme.typography.bodyLarge,
            )
        }
        SolventaTextField(
            value = state.value,
            onValueChange = onValueChange,
            label = stringResource(R.string.field_device_value),
            helper = if (state.gap == QuoteField.Value) required else "",
            state = if (state.gap == QuoteField.Value) SolventaFieldState.Error else SolventaFieldState.Default,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            testTag = "field_device_value",
        )
        SolventaTextField(
            value = state.brand,
            onValueChange = onBrandChange,
            label = stringResource(R.string.field_brand_model),
            helper = if (state.gap == QuoteField.Brand) required else "",
            state = if (state.gap == QuoteField.Brand) SolventaFieldState.Error else SolventaFieldState.Default,
            testTag = "field_brand_model",
        )
        Text(
            text = stringResource(R.string.field_older_than_12),
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.testTag("field_older_than_12"),
        )
        SolventaButton(
            text = stringResource(R.string.answer_yes),
            style = if (state.olderThan12Months == true) SolventaButtonStyle.Filled else SolventaButtonStyle.Tonal,
            onClick = { onAge(true) },
            testTag = "answer_yes",
        )
        SolventaButton(
            text = stringResource(R.string.answer_no),
            style = if (state.olderThan12Months == false) SolventaButtonStyle.Filled else SolventaButtonStyle.Tonal,
            onClick = { onAge(false) },
            testTag = "answer_no",
        )
        if (state.gap == QuoteField.Age) {
            Text(
                text = required,
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("age_required"),
            )
        }
        if (state.pending) {
            Text(
                text = stringResource(R.string.quote_progress),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("quote_progress"),
            )
        }
        if (state.failed) {
            Text(
                text = stringResource(R.string.quote_failed),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("quote_failed"),
            )
        }
        SolventaButton(
            text = stringResource(R.string.action_quote),
            style = SolventaButtonStyle.Filled,
            onClick = onCotizar,
            enabled = !state.pending,
            testTag = "action_quote",
        )
        SolventaButton(
            text = stringResource(R.string.action_secondary),
            style = SolventaButtonStyle.Outlined,
            onClick = onCancel,
            testTag = "action_cancel_quote",
        )
    }
}
