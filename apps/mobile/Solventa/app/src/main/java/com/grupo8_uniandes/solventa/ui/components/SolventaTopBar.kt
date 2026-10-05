package com.grupo8_uniandes.solventa.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun SolventaTopBar(
    title: String,
    showBack: Boolean,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface)
            .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Top))
            .heightIn(min = SolventaSpacing.minTouch)
            .padding(horizontal = SolventaSpacing.s8)
            .testTag(if (showBack) "top_bar_back" else "top_bar_root"),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (showBack) {
            SolventaIconButton(
                icon = painterResource(R.drawable.back),
                contentDescription = stringResource(R.string.action_back),
                onClick = onBack,
                testTag = "action_volver",
            )
        }
        Text(text = title, style = MaterialTheme.typography.titleMedium)
    }
}
