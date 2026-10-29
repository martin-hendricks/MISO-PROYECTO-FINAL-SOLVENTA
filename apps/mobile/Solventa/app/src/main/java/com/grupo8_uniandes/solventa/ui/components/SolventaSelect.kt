package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

enum class SolventaSelectAppearance {
    Button,
    Field,
}

@Composable
fun SolventaSelect(
    label: String,
    value: String,
    options: List<String>,
    expanded: Boolean,
    onExpandedChange: (Boolean) -> Unit,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier,
    appearance: SolventaSelectAppearance = SolventaSelectAppearance.Button,
) {
    val menuTag = if (expanded) "solventa_select_open" else "solventa_select_closed"
    if (appearance == SolventaSelectAppearance.Field) {
        DocumentTypeMenu(
            label = label,
            value = value,
            options = options,
            expanded = expanded,
            onExpandedChange = onExpandedChange,
            onSelect = onSelect,
            modifier = modifier,
            menuTag = menuTag,
        )
        return
    }
    Column(modifier.testTag(menuTag)) {
        SolventaButton(
            text = "$label: $value",
            style = SolventaButtonStyle.Outlined,
            onClick = { onExpandedChange(!expanded) },
            contentPadding = PaddingValues(horizontal = SolventaSpacing.s12),
        )
        if (expanded) {
            options.forEach { option ->
                Surface(
                    onClick = {
                        onSelect(option)
                        onExpandedChange(false)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = SolventaSpacing.minTouch)
                        .testTag("option_$option"),
                ) {
                    Text(option)
                }
            }
        }
    }
}

@Composable
private fun DocumentTypeMenu(
    label: String,
    value: String,
    options: List<String>,
    expanded: Boolean,
    onExpandedChange: (Boolean) -> Unit,
    onSelect: (String) -> Unit,
    modifier: Modifier,
    menuTag: String,
) {
    val shape = RoundedCornerShape(8.dp)
    Column(modifier.fillMaxWidth()) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(SolventaSpacing.s4))
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(SolventaSpacing.minTouch)
                .clip(shape)
                .background(MaterialTheme.colorScheme.surfaceContainerLowest)
                .border(1.dp, MaterialTheme.colorScheme.outlineVariant, shape)
                .clickable { onExpandedChange(!expanded) }
                .semantics { role = Role.DropdownList }
                .testTag(menuTag)
                .padding(horizontal = SolventaSpacing.s12),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = value,
                style = SolventaTypography.amount,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.weight(1f),
            )
            Icon(
                imageVector = Icons.Filled.ArrowDropDown,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        if (expanded) {
            options.forEach { option ->
                Surface(
                    onClick = {
                        onSelect(option)
                        onExpandedChange(false)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = SolventaSpacing.minTouch)
                        .testTag("option_$option"),
                ) {
                    Text(
                        text = option,
                        modifier = Modifier.padding(horizontal = SolventaSpacing.s12),
                    )
                }
            }
        }
    }
}
