package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuAnchorType
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteInput
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteLine
import com.grupo8_uniandes.solventa.quote.QuoteUiState
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CotizacionScreen(
    state: QuoteUiState,
    onMenu: (Boolean) -> Unit,
    onLine: (QuoteLine) -> Unit,
    onValueChange: (String) -> Unit,
    onBrandChange: (String) -> Unit,
    onAge: (Boolean) -> Unit,
    onText: (QuoteInput, String) -> Unit,
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
        ExposedDropdownMenuBox(
            expanded = state.menuOpen,
            onExpandedChange = onMenu,
        ) {
            OutlinedTextField(
                value = stringResource(state.line.label()),
                onValueChange = {},
                readOnly = true,
                label = { Text(stringResource(R.string.field_ramo)) },
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = state.menuOpen) },
                colors = ExposedDropdownMenuDefaults.outlinedTextFieldColors(),
                modifier = Modifier
                    .menuAnchor(ExposedDropdownMenuAnchorType.PrimaryNotEditable)
                    .fillMaxWidth()
                    .testTag("quote_line"),
            )
            ExposedDropdownMenu(
                expanded = state.menuOpen,
                onDismissRequest = { onMenu(false) },
                modifier = Modifier.testTag("quote_line_menu"),
            ) {
                QuoteLine.entries.forEach { line ->
                    DropdownMenuItem(
                        text = { Text(stringResource(line.label())) },
                        onClick = { onLine(line) },
                        modifier = Modifier.testTag(line.optionTag()),
                    )
                }
            }
        }
        if (state.line == QuoteLine.Device) {
            Text(
                text = stringResource(R.string.product_coverages),
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.testTag("quote_coverages"),
            )
            SolventaTextField(
                value = state.value,
                onValueChange = onValueChange,
                label = stringResource(R.string.field_device_value),
                helper = if (state.gap == QuoteInput.Value) required else "",
                state = if (state.gap == QuoteInput.Value) SolventaFieldState.Error else SolventaFieldState.Default,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                testTag = "field_device_value",
            )
            SolventaTextField(
                value = state.brand,
                onValueChange = onBrandChange,
                label = stringResource(R.string.field_brand_model),
                helper = if (state.gap == QuoteInput.Brand) required else "",
                state = if (state.gap == QuoteInput.Brand) SolventaFieldState.Error else SolventaFieldState.Default,
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
            if (state.gap == QuoteInput.Age) {
                Text(
                    text = required,
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.testTag("age_required"),
                )
            }
        } else {
            state.line.fields().forEach { field ->
                val numeric = field != QuoteInput.Destination &&
                    field != QuoteInput.Event &&
                    field != QuoteInput.Reference
                SolventaTextField(
                    value = state.textOf(field),
                    onValueChange = { onText(field, it) },
                    label = stringResource(field.label()),
                    helper = if (state.gap == field) required else "",
                    state = if (state.gap == field) SolventaFieldState.Error else SolventaFieldState.Default,
                    keyboardOptions = if (numeric) {
                        KeyboardOptions(keyboardType = KeyboardType.Number)
                    } else {
                        KeyboardOptions.Default
                    },
                    testTag = field.tag(),
                )
            }
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

private fun QuoteLine.label(): Int = when (this) {
    QuoteLine.Device -> R.string.line_device
    QuoteLine.Life -> R.string.line_life
    QuoteLine.Climate -> R.string.line_climate
    QuoteLine.Mortgage -> R.string.line_mortgage
    QuoteLine.Payments -> R.string.line_payments
    QuoteLine.Travel -> R.string.line_travel
}

private fun QuoteLine.optionTag(): String = when (this) {
    QuoteLine.Device -> "quote_option_device"
    QuoteLine.Life -> "quote_option_life"
    QuoteLine.Climate -> "quote_option_climate"
    QuoteLine.Mortgage -> "quote_option_mortgage"
    QuoteLine.Payments -> "quote_option_payments"
    QuoteLine.Travel -> "quote_option_travel"
}

private fun QuoteLine.fields(): List<QuoteInput> = when (this) {
    QuoteLine.Device -> emptyList()
    QuoteLine.Life -> listOf(QuoteInput.SumInsured, QuoteInput.AgeYears)
    QuoteLine.Climate -> listOf(QuoteInput.Event, QuoteInput.Reference, QuoteInput.Threshold)
    QuoteLine.Mortgage -> listOf(QuoteInput.CreditValue, QuoteInput.CreditTerm)
    QuoteLine.Payments -> listOf(QuoteInput.Installment, QuoteInput.Term)
    QuoteLine.Travel -> listOf(QuoteInput.Destination, QuoteInput.Duration)
}

private fun QuoteInput.label(): Int = when (this) {
    QuoteInput.Destination -> R.string.field_destination
    QuoteInput.Duration -> R.string.field_duration
    QuoteInput.SumInsured -> R.string.field_sum_insured
    QuoteInput.AgeYears -> R.string.field_age_years
    QuoteInput.Event -> R.string.field_event
    QuoteInput.Reference -> R.string.field_reference
    QuoteInput.Threshold -> R.string.field_threshold
    QuoteInput.Installment -> R.string.field_installment
    QuoteInput.Term -> R.string.field_term
    QuoteInput.CreditValue -> R.string.field_credit_value
    QuoteInput.CreditTerm -> R.string.field_credit_term
    QuoteInput.Value, QuoteInput.Brand, QuoteInput.Age -> R.string.field_required
}

private fun QuoteInput.tag(): String = when (this) {
    QuoteInput.Destination -> "field_destination"
    QuoteInput.Duration -> "field_duration"
    QuoteInput.SumInsured -> "field_sum_insured"
    QuoteInput.AgeYears -> "field_age_years"
    QuoteInput.Event -> "field_event"
    QuoteInput.Reference -> "field_reference"
    QuoteInput.Threshold -> "field_threshold"
    QuoteInput.Installment -> "field_installment"
    QuoteInput.Term -> "field_term"
    QuoteInput.CreditValue -> "field_credit_value"
    QuoteInput.CreditTerm -> "field_credit_term"
    QuoteInput.Value -> "field_device_value"
    QuoteInput.Brand -> "field_brand_model"
    QuoteInput.Age -> "field_older_than_12"
}

private fun QuoteUiState.textOf(field: QuoteInput): String = when (field) {
    QuoteInput.Destination -> destination
    QuoteInput.Duration -> duration
    QuoteInput.SumInsured -> sumInsured
    QuoteInput.AgeYears -> ageYears
    QuoteInput.Event -> event
    QuoteInput.Reference -> reference
    QuoteInput.Threshold -> threshold
    QuoteInput.Installment -> installment
    QuoteInput.Term -> term
    QuoteInput.CreditValue -> creditValue
    QuoteInput.CreditTerm -> creditTerm
    QuoteInput.Value -> value
    QuoteInput.Brand -> brand
    QuoteInput.Age -> ""
}
