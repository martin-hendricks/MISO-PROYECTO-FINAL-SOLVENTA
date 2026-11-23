package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun SolventaSkeleton(modifier: Modifier = Modifier) {
    val loading = stringResource(R.string.status_loading)
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(SolventaSpacing.s16)
            .background(MaterialTheme.colorScheme.surfaceContainerLow, SolventaSpacing.cardRadius)
            .testTag("solventa_skeleton")
            .clearAndSetSemantics { contentDescription = loading },
    )
}
