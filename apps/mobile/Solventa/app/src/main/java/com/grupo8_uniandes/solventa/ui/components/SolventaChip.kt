package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun SolventaChip(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    testTag: String = "solventa_chip",
    labelStyle: TextStyle? = null,
    showSelectionIcon: Boolean = true,
) {
    if (!showSelectionIcon) {
        ChoiceChip(
            label = label,
            selected = selected,
            onClick = onClick,
            modifier = modifier,
            testTag = testTag,
            labelStyle = labelStyle,
        )
        return
    }
    FilterChip(
        selected = selected,
        onClick = onClick,
        label = {
            if (labelStyle == null) {
                Text(label)
            } else {
                Text(label, style = labelStyle)
            }
        },
        modifier = modifier.testTag(testTag),
    )
}

@Composable
private fun ChoiceChip(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier,
    testTag: String,
    labelStyle: TextStyle?,
) {
    val shape = RoundedCornerShape(9999.dp)
    val container = if (selected) {
        MaterialTheme.colorScheme.secondaryContainer
    } else {
        Color.Transparent
    }
    val content = if (selected) {
        MaterialTheme.colorScheme.onSecondaryContainer
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant
    }
    val border = if (selected) {
        Modifier
    } else {
        Modifier.border(1.dp, MaterialTheme.colorScheme.outlineVariant, shape)
    }
    TextButton(
        onClick = onClick,
        modifier = modifier
            .then(border)
            .height(32.dp)
            .testTag(testTag),
        shape = shape,
        contentPadding = PaddingValues(horizontal = SolventaSpacing.s16, vertical = SolventaSpacing.s8),
        colors = ButtonDefaults.textButtonColors(
            containerColor = container,
            contentColor = content,
        ),
    ) {
        if (labelStyle == null) {
            Text(label)
        } else {
            Text(label, style = labelStyle)
        }
    }
}
