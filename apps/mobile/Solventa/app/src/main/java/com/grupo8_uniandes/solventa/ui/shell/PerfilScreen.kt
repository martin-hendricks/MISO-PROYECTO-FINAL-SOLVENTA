package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.data.consent.SharedPrefsConsentRepository
import com.grupo8_uniandes.solventa.data.region.SharedPrefsRegionRepository
import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import com.grupo8_uniandes.solventa.ui.components.SolventaListRow
import com.grupo8_uniandes.solventa.ui.consent.ConsentSheet
import com.grupo8_uniandes.solventa.ui.consent.ConsentSurface
import com.grupo8_uniandes.solventa.ui.consent.ConsentViewModel
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionSheet
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionViewModel
import com.grupo8_uniandes.solventa.ui.region.RegionSurface
import com.grupo8_uniandes.solventa.ui.region.findActivity
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun PerfilScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val repository = remember { SharedPrefsRegionRepository(context.applicationContext) }
    val viewModel = remember {
        IdiomaRegionViewModel(repository = repository, surface = RegionSurface.Profile)
    }
    val state by viewModel.state.collectAsState()
    var sheetOpen by remember { mutableStateOf(false) }
    val consentRepository = remember { SharedPrefsConsentRepository(context.applicationContext) }
    val consentViewModel = remember(consentRepository) {
        ConsentViewModel(
            change = ChangeDataTreatment(consentRepository) { System.currentTimeMillis() },
            initial = consentRepository.read(),
            surface = ConsentSurface.Profile,
        )
    }
    val consent by consentViewModel.state.collectAsState()
    var consentSheetOpen by remember { mutableStateOf(false) }
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
            onClick = {
                viewModel.syncToApplied()
                sheetOpen = true
            },
        )
        if (consent.stored != ConsentState.NotGranted) {
            SolventaListRow(
                label = stringResource(R.string.profile_consent),
                value = stringResource(
                    if (consent.stored == ConsentState.Granted) {
                        R.string.consent_state_granted
                    } else {
                        R.string.consent_state_revoked
                    },
                ),
                testTag = "profile_consent",
                onClick = {
                    consentViewModel.close()
                    consentSheetOpen = true
                },
            )
        }
    }
    IdiomaRegionSheet(
        visible = sheetOpen,
        draft = state.choice.draftRegion,
        onSelect = viewModel::select,
        onListo = {
            viewModel.confirm()
            context.findActivity()?.resumeProfileAfterLocaleChange()
        },
        onDismiss = {
            viewModel.dismiss()
            sheetOpen = false
        },
    )
    ConsentSheet(
        visible = consentSheetOpen,
        switchOn = consent.switchOn,
        confirmEnabled = consent.confirmEnabled,
        onSwitch = consentViewModel::onSwitch,
        onConfirm = {
            consentViewModel.confirm()
            consentSheetOpen = false
        },
        onClose = {
            consentViewModel.close()
            consentSheetOpen = false
        },
    )
}
