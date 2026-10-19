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
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun SiniestrosScreen(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SolventaSpacing.gutter)
            .testTag("screen_siniestros"),
    ) {
        Text(
            text = stringResource(R.string.destination_siniestros),
            style = MaterialTheme.typography.headlineMedium,
        )
        Text(
            text = stringResource(R.string.claims_placeholder),
            style = MaterialTheme.typography.bodyLarge,
        )
    }
}
