package com.grupo8_uniandes.solventa.ui.components

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
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun SolventaCard(
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    testTag: String = "solventa_card",
    content: @Composable ColumnScope.() -> Unit,
) {
    val cardModifier = modifier.fillMaxWidth().testTag(testTag)
    val shape = SolventaSpacing.cardRadius
    val colors = CardDefaults.cardColors(
        containerColor = MaterialTheme.colorScheme.surfaceContainerLow,
    )
    if (onClick == null) {
        Card(modifier = cardModifier, shape = shape, colors = colors) {
            Column(Modifier.padding(SolventaSpacing.gutter), content = content)
        }
    } else {
        Card(onClick = onClick, modifier = cardModifier, shape = shape, colors = colors) {
            Column(Modifier.padding(SolventaSpacing.gutter), content = content)
        }
    }
}
