package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaListRow
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun PerfilScreen(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .testTag("screen_perfil"),
    ) {
        Text(
            text = stringResource(R.string.destination_perfil),
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(SolventaSpacing.gutter),
        )
        SolventaListRow(
            label = stringResource(R.string.profile_language),
            testTag = "profile_entry",
        )
    }
}
