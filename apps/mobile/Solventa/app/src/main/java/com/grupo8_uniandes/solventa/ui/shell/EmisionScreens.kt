package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.activity.compose.BackHandler
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.sp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaBanner
import com.grupo8_uniandes.solventa.ui.components.SolventaBannerStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaStatus
import com.grupo8_uniandes.solventa.ui.components.SolventaStatusMark
import com.grupo8_uniandes.solventa.ui.theme.HankenGrotesk
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun EmisionEnCursoScreen(
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_emision"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        SolventaStatusMark(status = SolventaStatus.Processing)
        Text(
            text = stringResource(R.string.issuing_title),
            fontFamily = HankenGrotesk,
            fontWeight = FontWeight.SemiBold,
            fontSize = 24.sp,
            lineHeight = 32.sp,
            color = MaterialTheme.colorScheme.onSurface,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
        Text(
            text = stringResource(R.string.issuing_body),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier
                .fillMaxWidth()
                .testTag("emision_body"),
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
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_issued"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        SolventaStatusMark(status = SolventaStatus.Success)
        Text(
            text = stringResource(R.string.issued_title),
            fontFamily = HankenGrotesk,
            fontWeight = FontWeight.SemiBold,
            fontSize = 24.sp,
            lineHeight = 32.sp,
            color = MaterialTheme.colorScheme.onSurface,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
        Text(
            text = policyId,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
            textAlign = TextAlign.Center,
            modifier = Modifier
                .fillMaxWidth()
                .testTag("issued_policy_id"),
        )
        Text(
            text = stringResource(R.string.issued_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
        SolventaButton(
            text = stringResource(R.string.action_go_policy),
            style = SolventaButtonStyle.Filled,
            onClick = onGoPolicy,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_issued_policy",
        )
        SolventaButton(
            text = stringResource(R.string.action_go_home),
            style = SolventaButtonStyle.Tonal,
            onClick = onGoHome,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_issued_home",
        )
    }
}

@Composable
fun SuscripcionRechazadaScreen(
    onHome: () -> Unit,
    onUnderstood: () -> Unit,
    modifier: Modifier = Modifier,
) {
    BackHandler(onBack = onHome)
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_rejection"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        SolventaStatusMark(status = SolventaStatus.Error)
        Text(
            text = stringResource(R.string.rejection_title),
            fontFamily = HankenGrotesk,
            fontWeight = FontWeight.SemiBold,
            fontSize = 24.sp,
            lineHeight = 32.sp,
            color = MaterialTheme.colorScheme.onSurface,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
        Text(
            text = stringResource(R.string.rejection_heading),
            fontFamily = HankenGrotesk,
            fontWeight = FontWeight.Medium,
            fontSize = 20.sp,
            lineHeight = 26.sp,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.fillMaxWidth(),
        )
        SolventaBanner(
            message = stringResource(R.string.rejection_banner),
            style = SolventaBannerStyle.Error,
        )
        SolventaButton(
            text = stringResource(R.string.action_back_home),
            style = SolventaButtonStyle.Filled,
            onClick = onHome,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_rejection_home",
        )
        SolventaButton(
            text = stringResource(R.string.action_understood),
            style = SolventaButtonStyle.Text,
            onClick = onUnderstood,
            modifier = Modifier.fillMaxWidth(),
            testTag = "action_rejection_understood",
        )
    }
}
