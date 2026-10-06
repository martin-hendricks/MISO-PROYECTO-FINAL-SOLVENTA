package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaStatus
import com.grupo8_uniandes.solventa.ui.components.SolventaStatusIcon
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import com.grupo8_uniandes.solventa.ui.theme.SolventaTypography

@Composable
fun EmisionEnCursoScreen(
    onFinished: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SolventaSpacing.gutter)
            .testTag("screen_emision"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.issuing_title),
            style = MaterialTheme.typography.headlineMedium,
        )
        SolventaStatusIcon(
            status = SolventaStatus.Processing,
            word = stringResource(R.string.issuing_status),
            icon = painterResource(R.drawable.info),
        )
        SolventaButton(
            text = stringResource(R.string.action_continue_issued),
            style = SolventaButtonStyle.Filled,
            onClick = onFinished,
            testTag = "action_finish_issuing",
        )
    }
}

@Composable
fun PolizaEmitidaScreen(
    policyId: String,
    onGoHome: () -> Unit,
    onGoPolicy: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(SolventaSpacing.gutter)
            .testTag("screen_issued"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
    ) {
        Text(
            text = stringResource(R.string.issued_title),
            style = MaterialTheme.typography.headlineMedium,
        )
        SolventaStatusIcon(
            status = SolventaStatus.Success,
            word = stringResource(R.string.issued_status),
            icon = painterResource(R.drawable.check),
        )
        Text(text = policyId, style = SolventaTypography.amount)
        SolventaButton(
            text = stringResource(R.string.action_go_home),
            style = SolventaButtonStyle.Filled,
            onClick = onGoHome,
            testTag = "action_issued_home",
        )
        SolventaButton(
            text = stringResource(R.string.action_go_policy),
            style = SolventaButtonStyle.Outlined,
            onClick = onGoPolicy,
            testTag = "action_issued_policy",
        )
    }
}
