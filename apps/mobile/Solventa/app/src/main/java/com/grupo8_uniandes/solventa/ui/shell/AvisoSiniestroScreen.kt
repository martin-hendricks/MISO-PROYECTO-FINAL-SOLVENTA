package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

object AvisoChrome {
    var titleRes by mutableIntStateOf(R.string.claim_evidence_title)
    var coverTabs by mutableStateOf(false)

    fun reset() {
        titleRes = R.string.claim_evidence_title
        coverTabs = false
    }
}

@Composable
fun AvisoSiniestroScreen(
    onContinue: () -> Unit,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_aviso_siniestro"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.claim_notice_explanation),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        SolventaTextField(
            value = stringResource(R.string.claim_notice_policy_value),
            onValueChange = {},
            label = stringResource(R.string.claim_notice_policy_label),
            helper = stringResource(R.string.claim_notice_policy_help),
            state = SolventaFieldState.ReadOnly,
            externalLabel = true,
            testTag = "claim_policy",
        )
        SolventaTextField(
            value = stringResource(R.string.claim_notice_date_value),
            onValueChange = {},
            label = stringResource(R.string.claim_notice_date_label),
            helper = "",
            state = SolventaFieldState.ReadOnly,
            externalLabel = true,
            testTag = "claim_date",
        )
        SolventaTextField(
            value = stringResource(R.string.claim_notice_description_value),
            onValueChange = {},
            label = stringResource(R.string.claim_notice_description_label),
            helper = "",
            state = SolventaFieldState.ReadOnly,
            externalLabel = true,
            testTag = "claim_description",
        )
        SolventaTextField(
            value = stringResource(R.string.claim_notice_place_value),
            onValueChange = {},
            label = stringResource(R.string.claim_notice_place_label),
            helper = stringResource(R.string.claim_notice_place_help),
            state = SolventaFieldState.ReadOnly,
            externalLabel = true,
            testTag = "claim_place",
        )
        SolventaButton(
            text = stringResource(R.string.claim_notice_continue),
            style = SolventaButtonStyle.Filled,
            onClick = onContinue,
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_continue",
        )
        SolventaButton(
            text = stringResource(R.string.claim_notice_cancel),
            style = SolventaButtonStyle.Outlined,
            onClick = onCancel,
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_cancel",
        )
    }
}
