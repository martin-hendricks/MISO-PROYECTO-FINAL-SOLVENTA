package com.grupo8_uniandes.solventa.ui.region

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaIconButton
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun IdiomaRegionScreen(
    draft: Region,
    onSelect: (Region) -> Unit,
    onContinue: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface)
            .verticalScroll(rememberScrollState())
            .padding(SolventaSpacing.gutter)
            .testTag("screen_idioma_region"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            SolventaIconButton(
                icon = painterResource(R.drawable.back),
                contentDescription = stringResource(R.string.action_back),
                onClick = onBack,
                testTag = "idioma_back",
            )
            Text(
                text = stringResource(R.string.idioma_title),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
        Text(
            text = stringResource(R.string.idioma_heading),
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
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
            text = stringResource(R.string.action_continuar_region),
            style = SolventaButtonStyle.Filled,
            onClick = onContinue,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_continuar",
        )
    }
}

@Composable
internal fun regionOptions(): List<RegionOptionCopy> = listOf(
    RegionOptionCopy(
        Region.Colombia,
        stringResource(R.string.region_name_co),
        stringResource(R.string.region_example_co),
    ),
    RegionOptionCopy(
        Region.Mexico,
        stringResource(R.string.region_name_mx),
        stringResource(R.string.region_example_mx),
    ),
    RegionOptionCopy(
        Region.Chile,
        stringResource(R.string.region_name_cl),
        stringResource(R.string.region_example_cl),
    ),
    RegionOptionCopy(
        Region.Peru,
        stringResource(R.string.region_name_pe),
        stringResource(R.string.region_example_pe),
    ),
)

internal data class RegionOptionCopy(
    val region: Region,
    val name: String,
    val example: String,
)

@Composable
internal fun RegionOptionRow(
    option: RegionOptionCopy,
    selected: Boolean,
    onSelect: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val border = if (selected) {
        MaterialTheme.colorScheme.primary
    } else {
        MaterialTheme.colorScheme.outlineVariant
    }
    val fill = if (selected) {
        MaterialTheme.colorScheme.secondaryContainer
    } else {
        MaterialTheme.colorScheme.surfaceContainerLowest
    }
    Row(
        modifier = modifier
            .fillMaxWidth()
            .semantics { this.selected = selected }
            .testTag(option.region.rowTag())
            .clickable(onClick = onSelect)
            .border(width = 2.dp, color = border, shape = SolventaSpacing.cardRadius)
            .background(fill, SolventaSpacing.cardRadius)
            .padding(SolventaSpacing.gutter),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
    ) {
        if (selected) {
            Icon(
                painter = painterResource(R.drawable.check),
                contentDescription = option.name,
                tint = MaterialTheme.colorScheme.onSecondaryContainer,
                modifier = Modifier.testTag("region_check"),
            )
        } else {
            Icon(
                painter = painterResource(R.drawable.info),
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.testTag("region_info"),
            )
        }
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = option.name,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Text(
                text = option.example,
                style = SolventaTypography.amount,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
        Icon(
            painter = painterResource(R.drawable.chevron_right),
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

internal fun Region.rowTag(): String = "region_${languageTag.replace('-', '_')}"
