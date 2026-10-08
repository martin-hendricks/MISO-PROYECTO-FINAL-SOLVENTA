package com.grupo8_uniandes.solventa.ui.region

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomSheet
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun IdiomaRegionSheet(
    visible: Boolean,
    draft: Region,
    onSelect: (Region) -> Unit,
    onListo: () -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
) {
    SolventaBottomSheet(
        visible = visible,
        onDismiss = onDismiss,
        modifier = modifier,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
        ) {
            Text(
                text = stringResource(R.string.idioma_helper),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            regionOptions().forEach { option ->
                RegionOptionRow(
                    option = option,
                    selected = option.region == draft,
                    onSelect = { onSelect(option.region) },
                )
            }
            SolventaButton(
                text = stringResource(R.string.action_listo),
                style = SolventaButtonStyle.Filled,
                onClick = onListo,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_listo",
            )
        }
    }
}
