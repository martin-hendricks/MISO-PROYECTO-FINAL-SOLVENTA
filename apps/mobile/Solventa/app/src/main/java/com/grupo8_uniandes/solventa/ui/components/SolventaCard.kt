package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun SolventaCard(
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    outlined: Boolean = false,
    testTag: String = "solventa_card",
    content: @Composable ColumnScope.() -> Unit,
) {
    val cardModifier = modifier.fillMaxWidth().testTag(testTag)
    val shape = SolventaSpacing.cardRadius
    val colors = CardDefaults.cardColors(
        containerColor = if (outlined) {
            MaterialTheme.colorScheme.surfaceContainerLowest
        } else {
            MaterialTheme.colorScheme.surfaceContainerLow
        },
    )
    val border = if (outlined) BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant) else null
    val body: @Composable ColumnScope.() -> Unit = {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(SolventaSpacing.gutter),
            verticalArrangement = if (outlined) Arrangement.spacedBy(SolventaSpacing.s8) else Arrangement.Top,
            content = content,
        )
    }
    if (onClick == null) {
        Card(modifier = cardModifier, shape = shape, colors = colors, border = border, content = body)
    } else {
        Card(
            onClick = onClick,
            modifier = cardModifier,
            shape = shape,
            colors = colors,
            border = border,
            content = body,
        )
    }
}
