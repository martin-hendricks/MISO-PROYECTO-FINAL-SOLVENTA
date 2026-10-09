package com.grupo8_uniandes.solventa.ui.consent

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomSheet
import com.grupo8_uniandes.solventa.ui.components.SolventaIconButton
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun ConsentSheet(
    visible: Boolean,
    switchOn: Boolean,
    confirmEnabled: Boolean,
    onSwitch: (Boolean) -> Unit,
    onConfirm: () -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier,
) {
    SolventaBottomSheet(
        visible = visible,
        onDismiss = onClose,
        modifier = modifier,
    ) {
        BackHandler(onBack = onClose)
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                SolventaIconButton(
                    icon = painterResource(R.drawable.cancel),
                    contentDescription = stringResource(R.string.action_close),
                    onClick = onClose,
                    testTag = "action_close",
                )
            }
            ConsentBody(
                switchOn = switchOn,
                confirmEnabled = confirmEnabled,
                onSwitch = onSwitch,
                onConfirm = onConfirm,
            )
        }
    }
}
