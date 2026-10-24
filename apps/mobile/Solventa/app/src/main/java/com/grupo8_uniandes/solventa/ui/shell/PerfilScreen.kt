package com.grupo8_uniandes.solventa.ui.shell

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.data.consent.SharedPrefsConsentRepository
import com.grupo8_uniandes.solventa.data.profile.AndroidDevicePermissionReader
import com.grupo8_uniandes.solventa.data.profile.SharedPrefsSessionRepository
import com.grupo8_uniandes.solventa.data.region.SharedPrefsRegionRepository
import com.grupo8_uniandes.solventa.data.registration.SharedPrefsRegistrationRepository
import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import com.grupo8_uniandes.solventa.domain.profile.DevicePermissionReader
import com.grupo8_uniandes.solventa.domain.profile.LoadProfile
import com.grupo8_uniandes.solventa.domain.profile.PermissionKind
import com.grupo8_uniandes.solventa.domain.profile.SignOut
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomSheet
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaIconButton
import com.grupo8_uniandes.solventa.ui.components.SolventaListRow
import com.grupo8_uniandes.solventa.ui.consent.ConsentSheet
import com.grupo8_uniandes.solventa.ui.consent.ConsentSurface
import com.grupo8_uniandes.solventa.ui.consent.ConsentViewModel
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionSheet
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionViewModel
import com.grupo8_uniandes.solventa.ui.region.RegionSurface
import com.grupo8_uniandes.solventa.ui.region.findActivity
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import androidx.compose.foundation.layout.Row
import androidx.compose.ui.Alignment
import androidx.compose.ui.res.painterResource

@Composable
fun PerfilScreen(
    modifier: Modifier = Modifier,
    originationActive: Boolean = false,
    permissionReader: DevicePermissionReader? = null,
    onSignedOut: () -> Unit = {},
) {
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
    val profileViewModel: ProfileViewModel = viewModel(
        key = "profile-$originationActive",
        factory = profileFactory(context, originationActive, permissionReader),
    )
    val hub by profileViewModel.state.collectAsState()
    val signedOut by profileViewModel.signedOut.collectAsState()
    var permissionKind by remember { mutableStateOf<PermissionKind?>(null) }
    var profilingOpen by remember { mutableStateOf(false) }
    var signOutOpen by remember { mutableStateOf(false) }
    LaunchedEffect(signedOut) {
        if (signedOut) onSignedOut()
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .testTag("screen_perfil"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        hub.identity?.let { identity ->
            Column(
                modifier = Modifier
                    .padding(horizontal = SolventaSpacing.gutter)
                    .testTag("profile_identity"),
            ) {
                Text(text = identity.name, style = MaterialTheme.typography.titleMedium)
                Text(text = identity.document, style = MaterialTheme.typography.bodyMedium)
            }
        }
        SolventaListRow(
            label = stringResource(R.string.profile_language),
            supporting = stringResource(regionDetail(hub.region)),
            testTag = "profile_entry",
            onClick = {
                viewModel.syncToApplied()
                sheetOpen = true
            },
        )
        PermissionKind.entries.forEach { kind ->
            val published = hub.permissions.firstOrNull { it.kind == kind }?.published == true
            SolventaListRow(
                label = stringResource(permissionLabel(kind)),
                supporting = permissionDetail(kind, published),
                testTag = permissionTag(kind),
                onClick = { permissionKind = kind },
            )
        }
        if (consent.stored != ConsentState.NotGranted) {
            SolventaListRow(
                label = stringResource(R.string.profile_consent),
                supporting = stringResource(
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
        if (hub.originationActive) {
            SolventaListRow(
                label = stringResource(R.string.profile_profiling),
                testTag = "profile_profiling",
                onClick = { profilingOpen = true },
            )
        }
        SolventaButton(
            text = stringResource(R.string.action_sign_out),
            style = SolventaButtonStyle.Outlined,
            onClick = { signOutOpen = true },
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = SolventaSpacing.gutter),
            testTag = "action_sign_out",
        )
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
    val openKind = permissionKind
    StatusSheet(
        visible = openKind != null,
        title = openKind?.let { stringResource(permissionLabel(it)) }.orEmpty(),
        detail = openKind?.let { kind ->
            val published = hub.permissions.firstOrNull { it.kind == kind }?.published == true
            permissionDetail(kind, published)
        },
        sheetTag = "sheet_permission",
        onClose = { permissionKind = null },
    )
    StatusSheet(
        visible = profilingOpen,
        title = stringResource(R.string.profile_profiling),
        detail = null,
        sheetTag = "sheet_profiling",
        onClose = { profilingOpen = false },
    )
    SignOutSheet(
        visible = signOutOpen,
        onConfirm = {
            signOutOpen = false
            profileViewModel.confirmSignOut()
        },
        onCancel = { signOutOpen = false },
    )
}

@Composable
private fun permissionDetail(kind: PermissionKind, published: Boolean): String? {
    if (!published) return null
    val res = if (kind == PermissionKind.Photos) {
        R.string.profile_photos_notice
    } else {
        R.string.profile_permission_while_using
    }
    return stringResource(res)
}

private fun permissionLabel(kind: PermissionKind): Int = when (kind) {
    PermissionKind.Location -> R.string.profile_location
    PermissionKind.Camera -> R.string.profile_camera
    PermissionKind.Photos -> R.string.profile_photos
}

private fun permissionTag(kind: PermissionKind): String = when (kind) {
    PermissionKind.Location -> "profile_location"
    PermissionKind.Camera -> "profile_camera"
    PermissionKind.Photos -> "profile_photos"
}

private fun regionDetail(region: Region): Int = when (region) {
    Region.Colombia -> R.string.profile_region_co
    Region.Mexico -> R.string.profile_region_mx
    Region.Chile -> R.string.profile_region_cl
    Region.Peru -> R.string.profile_region_pe
}

@Composable
private fun StatusSheet(
    visible: Boolean,
    title: String,
    detail: String?,
    sheetTag: String,
    onClose: () -> Unit,
) {
    SolventaBottomSheet(visible = visible, onDismiss = onClose) {
        BackHandler(onBack = onClose)
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(SolventaSpacing.gutter)
                .testTag(sheetTag),
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
            Text(text = title, style = MaterialTheme.typography.titleMedium)
            if (detail != null) {
                Text(text = detail, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
private fun SignOutSheet(
    visible: Boolean,
    onConfirm: () -> Unit,
    onCancel: () -> Unit,
) {
    SolventaBottomSheet(visible = visible, onDismiss = onCancel) {
        BackHandler(onBack = onCancel)
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(SolventaSpacing.gutter)
                .testTag("sheet_sign_out"),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
        ) {
            Text(
                text = stringResource(R.string.action_sign_out),
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = stringResource(R.string.sign_out_body),
                style = MaterialTheme.typography.bodyMedium,
            )
            SolventaButton(
                text = stringResource(R.string.action_sign_out),
                style = SolventaButtonStyle.Filled,
                onClick = onConfirm,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_sign_out_confirm",
            )
            SolventaButton(
                text = stringResource(R.string.action_secondary),
                style = SolventaButtonStyle.Outlined,
                onClick = onCancel,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_sign_out_cancel",
            )
        }
    }
}

private fun profileFactory(
    context: android.content.Context,
    originationActive: Boolean,
    permissionReader: DevicePermissionReader?,
): ViewModelProvider.Factory = object : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        val appContext = context.applicationContext
        val session = SharedPrefsSessionRepository(appContext)
        val load = LoadProfile(
            registration = SharedPrefsRegistrationRepository(appContext),
            region = SharedPrefsRegionRepository(appContext),
            permissions = permissionReader ?: AndroidDevicePermissionReader(appContext),
            consent = SharedPrefsConsentRepository(appContext),
            session = session,
            originationActive = originationActive,
        )
        @Suppress("UNCHECKED_CAST")
        return ProfileViewModel(load = load, signOut = SignOut(session)) as T
    }
}
