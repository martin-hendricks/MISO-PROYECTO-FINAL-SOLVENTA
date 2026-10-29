package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteInput
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteLine
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.quoteAmountDigits
import com.grupo8_uniandes.solventa.quote.QuoteUiState
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaChip
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.HankenGrotesk
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

private val quoteMenu = listOf(
    QuoteLine.Device,
    QuoteLine.Travel,
    QuoteLine.Life,
    QuoteLine.Climate,
    QuoteLine.Payments,
    QuoteLine.Mortgage,
)

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
    region: Region = Region.Colombia,
    modifier: Modifier = Modifier,
) {
    val required = stringResource(R.string.field_required)
    val currency = region.currencyCode
    val moneyVisual = remember(region) { QuoteAmountVisualTransformation(region) }
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_cotizacion"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        InsuranceTypeSelect(state = state, onMenu = onMenu, onLine = onLine)
        if (state.line == QuoteLine.Device) {
            SolventaTextField(
                value = state.value,
                onValueChange = { onValueChange(quoteAmountDigits(it)) },
                label = stringResource(R.string.field_device_value, currency),
                helper = if (state.gap == QuoteInput.Value) required else "",
                state = if (state.gap == QuoteInput.Value) SolventaFieldState.Error else SolventaFieldState.Default,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                visualTransformation = moneyVisual,
                externalLabel = true,
                testTag = "field_device_value",
            )
            SolventaTextField(
                value = state.brand,
                onValueChange = onBrandChange,
                label = stringResource(R.string.field_brand_model),
                helper = if (state.gap == QuoteInput.Brand) required else "",
                state = if (state.gap == QuoteInput.Brand) SolventaFieldState.Error else SolventaFieldState.Default,
                externalLabel = true,
                testTag = "field_brand_model",
            )
            DeviceAge(olderThan12Months = state.olderThan12Months, onAge = onAge)
            if (state.gap == QuoteInput.Age) {
                Text(
                    text = required,
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.testTag("age_required"),
                )
            }
        } else {
            state.line.fields().forEach { field ->
                val numeric = field != QuoteInput.Destination && field != QuoteInput.Event
                val money = field.isMoney()
                val raw = state.textOf(field)
                SolventaTextField(
                    value = raw,
                    onValueChange = { typed ->
                        onText(field, if (money) quoteAmountDigits(typed) else typed)
                    },
                    visualTransformation = if (money) moneyVisual else VisualTransformation.None,
                    label = field.label(currency),
                    helper = if (state.gap == field) required else "",
                    state = if (state.gap == field) SolventaFieldState.Error else SolventaFieldState.Default,
                    keyboardOptions = if (numeric) {
                        KeyboardOptions(keyboardType = KeyboardType.Number)
                    } else {
                        KeyboardOptions.Default
                    },
                    externalLabel = true,
                    testTag = field.tag(),
                )
            }
        }
        Text(
            text = stringResource(R.string.quote_ramo_note),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.testTag("quote_ramo_note"),
        )
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
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_quote",
        )
        SolventaButton(
            text = stringResource(R.string.action_secondary),
            style = SolventaButtonStyle.Text,
            onClick = onCancel,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_cancel_quote",
        )
    }
}

@Composable
private fun InsuranceTypeSelect(
    state: QuoteUiState,
    onMenu: (Boolean) -> Unit,
    onLine: (QuoteLine) -> Unit,
) {
    val fieldShape = RoundedCornerShape(4.dp)
    val menuShape = RoundedCornerShape(8.dp)
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.field_ramo),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(SolventaSpacing.minTouch)
                .clip(fieldShape)
                .background(MaterialTheme.colorScheme.surfaceContainerLowest)
                .border(1.dp, MaterialTheme.colorScheme.outline, fieldShape)
                .clickable { onMenu(!state.menuOpen) }
                .semantics { role = Role.DropdownList }
                .testTag("quote_line")
                .padding(SolventaSpacing.s12),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
        ) {
            Text(
                text = stringResource(state.line.label()),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.weight(1f),
            )
            Icon(
                imageVector = if (state.menuOpen) Icons.Filled.ExpandLess else Icons.Filled.ExpandMore,
                contentDescription = null,
                modifier = Modifier.size(24.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Text(
            text = stringResource(state.line.hint()),
            style = TextStyle(
                fontFamily = HankenGrotesk,
                fontWeight = FontWeight.Normal,
                fontSize = 13.sp,
                lineHeight = 18.sp,
            ),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier
                .fillMaxWidth()
                .testTag("quote_line_hint"),
        )
        if (state.menuOpen) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(menuShape)
                    .background(MaterialTheme.colorScheme.surfaceContainerLowest)
                    .border(1.dp, MaterialTheme.colorScheme.outlineVariant, menuShape)
                    .testTag("quote_line_menu"),
            ) {
                quoteMenu.forEach { line ->
                    val selected = line == state.line
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(40.dp)
                            .background(
                                if (selected) {
                                    MaterialTheme.colorScheme.secondaryContainer
                                } else {
                                    MaterialTheme.colorScheme.surfaceContainerLowest
                                },
                            )
                            .clickable { onLine(line) }
                            .padding(horizontal = SolventaSpacing.s12)
                            .testTag(line.optionTag()),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
                    ) {
                        Text(
                            text = stringResource(line.label()),
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.onSurface,
                            modifier = Modifier.weight(1f),
                        )
                        if (selected) {
                            Icon(
                                imageVector = Icons.Filled.Check,
                                contentDescription = null,
                                modifier = Modifier.size(20.dp),
                                tint = MaterialTheme.colorScheme.primary,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun DeviceAge(
    olderThan12Months: Boolean?,
    onAge: (Boolean) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s8)) {
        Text(
            text = stringResource(R.string.field_older_than_12),
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.testTag("field_older_than_12"),
        )
        Row(horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8)) {
            SolventaChip(
                label = stringResource(R.string.answer_yes),
                selected = olderThan12Months == true,
                onClick = { onAge(true) },
                testTag = "answer_yes",
                labelStyle = SolventaTypography.amount,
                showSelectionIcon = false,
            )
            SolventaChip(
                label = stringResource(R.string.answer_no),
                selected = olderThan12Months == false,
                onClick = { onAge(false) },
                testTag = "answer_no",
                labelStyle = SolventaTypography.amount,
                showSelectionIcon = false,
            )
        }
    }
}

@Composable
private fun QuoteInput.label(currency: String): String = when (this) {
    QuoteInput.Destination -> stringResource(R.string.field_destination)
    QuoteInput.Duration -> stringResource(R.string.field_duration)
    QuoteInput.SumInsured -> stringResource(R.string.field_sum_insured, currency)
    QuoteInput.AgeYears -> stringResource(R.string.field_age_years)
    QuoteInput.Event -> stringResource(R.string.field_event)
    QuoteInput.Threshold -> stringResource(R.string.field_threshold)
    QuoteInput.Installment -> stringResource(R.string.field_installment, currency)
    QuoteInput.Term -> stringResource(R.string.field_term)
    QuoteInput.CreditValue -> stringResource(R.string.field_credit_value, currency)
    QuoteInput.CreditTerm -> stringResource(R.string.field_credit_term)
    QuoteInput.Reference, QuoteInput.Value, QuoteInput.Brand, QuoteInput.Age ->
        stringResource(R.string.field_required)
}

private fun QuoteInput.isMoney(): Boolean = this == QuoteInput.Value ||
    this == QuoteInput.SumInsured ||
    this == QuoteInput.CreditValue ||
    this == QuoteInput.Installment

private fun QuoteLine.label(): Int = when (this) {
    QuoteLine.Device -> R.string.line_device
    QuoteLine.Life -> R.string.line_life
    QuoteLine.Climate -> R.string.line_climate
    QuoteLine.Mortgage -> R.string.line_mortgage
    QuoteLine.Payments -> R.string.line_payments
    QuoteLine.Travel -> R.string.line_travel
}

private fun QuoteLine.hint(): Int = when (this) {
    QuoteLine.Device -> R.string.hint_line_device
    QuoteLine.Life -> R.string.hint_line_life
    QuoteLine.Climate -> R.string.hint_line_climate
    QuoteLine.Mortgage -> R.string.hint_line_mortgage
    QuoteLine.Payments -> R.string.hint_line_payments
    QuoteLine.Travel -> R.string.hint_line_travel
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
    QuoteLine.Climate -> listOf(QuoteInput.Event, QuoteInput.Threshold)
    QuoteLine.Mortgage -> listOf(QuoteInput.CreditValue, QuoteInput.CreditTerm)
    QuoteLine.Payments -> listOf(QuoteInput.Installment, QuoteInput.Term)
    QuoteLine.Travel -> listOf(QuoteInput.Destination, QuoteInput.Duration)
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
