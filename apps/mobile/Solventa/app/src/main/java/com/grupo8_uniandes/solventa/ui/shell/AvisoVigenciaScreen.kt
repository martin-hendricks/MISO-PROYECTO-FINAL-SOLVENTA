package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityKind
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityReading
import com.grupo8_uniandes.solventa.ui.components.SolventaBanner
import com.grupo8_uniandes.solventa.ui.components.SolventaBannerStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun AvisoVigenciaScreen(
    reading: ValidityReading,
    onViewPolicy: () -> Unit,
    onLeave: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val tag = when (reading.kind) {
        ValidityKind.EXPIRY -> "screen_aviso_vencimiento"
        ValidityKind.RENEWAL -> "screen_aviso_renovacion"
    }
    val secondary = when (reading.kind) {
        ValidityKind.EXPIRY -> stringResource(R.string.action_understood)
        ValidityKind.RENEWAL -> stringResource(R.string.action_go_home)
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .testTag(tag)
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        SolventaBanner(
            message = reading.banner,
            style = SolventaBannerStyle.Info,
        )
        SolventaButton(
            text = stringResource(R.string.action_view_policy),
            style = SolventaButtonStyle.Filled,
            onClick = onViewPolicy,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_view_policy",
        )
        SolventaButton(
            text = secondary,
            style = SolventaButtonStyle.Text,
            onClick = onLeave,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_leave_notice",
        )
    }
}
