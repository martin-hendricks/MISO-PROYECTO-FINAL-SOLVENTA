package com.grupo8_uniandes.solventa.ui.shell

import android.content.Intent
import android.net.Uri
import android.provider.Settings
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNoticeDraft
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaListRow
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun EvidenciaAvisoScreen(
    phase: NoticePhase,
    draft: ClaimNoticeDraft,
    onAllowCamera: () -> Unit,
    onDenyCamera: () -> Unit,
    onDismissCamera: () -> Unit,
    onAllowPhotos: () -> Unit,
    onDenyPhotos: () -> Unit,
    onAllowLocation: () -> Unit,
    onDenyLocation: () -> Unit,
    onDismissLocation: () -> Unit,
    onOpenLocation: () -> Unit,
    onChoosePhotos: () -> Unit,
    onSend: () -> Unit,
    onQueue: () -> Unit,
    onAttach: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    SideEffect {
        AvisoChrome.titleRes = phase.titleRes()
        AvisoChrome.coverTabs = phase.coversTabs()
    }
    DisposableEffect(Unit) {
        onDispose { AvisoChrome.reset() }
    }
    Box(
        modifier = modifier
            .fillMaxSize()
            .testTag("screen_evidencia_aviso"),
    ) {
        when (phase) {
            NoticePhase.Camera -> PermissionAsk(
                heading = stringResource(R.string.claim_camera_heading),
                body = stringResource(R.string.claim_camera_body),
                allow = stringResource(R.string.claim_camera_allow),
                dialogTitle = stringResource(R.string.claim_camera_dialog_title),
                dialogBody = stringResource(R.string.claim_camera_dialog_body),
                primary = stringResource(R.string.claim_permission_while_using),
                secondary = stringResource(R.string.claim_permission_once),
                onAllow = onAllowCamera,
                onDeny = onDenyCamera,
                onNotNow = onDismissCamera,
            )
            NoticePhase.Photos -> PermissionAsk(
                heading = stringResource(R.string.claim_photos_heading),
                body = stringResource(R.string.claim_photos_body),
                allow = stringResource(R.string.claim_photos_allow),
                dialogTitle = stringResource(R.string.claim_photos_dialog_title),
                dialogBody = stringResource(R.string.claim_photos_dialog_body),
                primary = stringResource(R.string.claim_photos_all),
                secondary = stringResource(R.string.claim_photos_select),
                onAllow = onAllowPhotos,
                onDeny = onDenyPhotos,
                onNotNow = onDenyPhotos,
            )
            NoticePhase.Location -> PermissionAsk(
                heading = stringResource(R.string.claim_location_heading),
                body = stringResource(R.string.claim_location_body),
                allow = stringResource(R.string.claim_location_allow),
                dialogTitle = stringResource(R.string.claim_location_dialog_title),
                dialogBody = stringResource(R.string.claim_location_dialog_body),
                primary = stringResource(R.string.claim_permission_while_using),
                secondary = stringResource(R.string.claim_permission_once),
                onAllow = onAllowLocation,
                onDeny = onDenyLocation,
                onNotNow = onDismissLocation,
            )
            else -> EvidenceBody(
                phase = phase,
                draft = draft,
                onOpenLocation = onOpenLocation,
                onChoosePhotos = onChoosePhotos,
                onSettings = {
                    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                        data = Uri.fromParts("package", context.packageName, null)
                    }
                    context.startActivity(intent)
                },
                onSend = onSend,
                onQueue = onQueue,
                onAttach = onAttach,
            )
        }
    }
}

private fun NoticePhase.titleRes(): Int = when (this) {
    NoticePhase.Camera -> R.string.claim_camera_title
    NoticePhase.Photos -> R.string.claim_photos_title
    NoticePhase.Location -> R.string.claim_location_title
    NoticePhase.GeoDenied -> R.string.claim_geo_denied_title
    NoticePhase.CameraDenied -> R.string.claim_camera_denied_title
    else -> R.string.claim_evidence_title
}

private fun NoticePhase.coversTabs(): Boolean = when (this) {
    NoticePhase.Camera, NoticePhase.Photos, NoticePhase.Location -> true
    else -> false
}

@Composable
private fun EvidenceBody(
    phase: NoticePhase,
    draft: ClaimNoticeDraft,
    onOpenLocation: () -> Unit,
    onChoosePhotos: () -> Unit,
    onSettings: () -> Unit,
    onSend: () -> Unit,
    onQueue: () -> Unit,
    onAttach: () -> Unit,
) {
    val deniedCamera = phase == NoticePhase.CameraDenied
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(88.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(MaterialTheme.colorScheme.surfaceContainerHighest)
                .testTag("claim_evidence_preview"),
        )
        val locationTitle = when {
            draft.geo != null -> stringResource(R.string.claim_location_added)
            draft.locationDenied -> stringResource(R.string.claim_geo_denied)
            deniedCamera -> stringResource(R.string.claim_camera_denied)
            else -> stringResource(R.string.claim_notice_place_label)
        }
        val locationHelp = when {
            draft.geo != null -> stringResource(R.string.claim_location_coordinate)
            draft.locationDenied -> stringResource(R.string.claim_geo_denied_help)
            deniedCamera -> stringResource(R.string.claim_camera_denied_help)
            else -> stringResource(R.string.claim_notice_place_help)
        }
        SolventaListRow(
            label = locationTitle,
            supporting = locationHelp,
            onClick = onOpenLocation,
            testTag = "claim_location_row",
        )
        Text(
            text = if (draft.locationDenied || deniedCamera) {
                stringResource(R.string.claim_photo_caption)
            } else {
                stringResource(R.string.claim_evidence_body)
            },
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        if (!draft.locationDenied && !deniedCamera) {
            Text(
                text = stringResource(R.string.claim_scan_body),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        if (deniedCamera) {
            SolventaButton(
                text = stringResource(R.string.claim_choose_photos),
                style = SolventaButtonStyle.Filled,
                onClick = onChoosePhotos,
                modifier = Modifier.fillMaxWidth(),
                testTag = "claim_choose_photos",
            )
            SolventaButton(
                text = stringResource(R.string.claim_open_settings),
                style = SolventaButtonStyle.Tonal,
                onClick = onSettings,
                modifier = Modifier.fillMaxWidth(),
            )
        } else {
            SolventaButton(
                text = stringResource(R.string.claim_evidence_send),
                style = SolventaButtonStyle.Filled,
                onClick = onSend,
                modifier = Modifier.fillMaxWidth(),
                testTag = "claim_send",
            )
            if (!draft.locationDenied) {
                SolventaButton(
                    text = stringResource(R.string.claim_scan_attach),
                    style = SolventaButtonStyle.Tonal,
                    onClick = onAttach,
                    modifier = Modifier.fillMaxWidth(),
                    testTag = "claim_attach",
                )
            } else {
                SolventaButton(
                    text = stringResource(R.string.claim_open_settings),
                    style = SolventaButtonStyle.Tonal,
                    onClick = onSettings,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
            SolventaButton(
                text = stringResource(R.string.claim_evidence_queue),
                style = SolventaButtonStyle.Tonal,
                onClick = onQueue,
                modifier = Modifier.fillMaxWidth(),
                testTag = "claim_queue",
            )
        }
    }
}

@Composable
private fun PermissionAsk(
    heading: String,
    body: String,
    allow: String,
    dialogTitle: String,
    dialogBody: String,
    primary: String,
    secondary: String,
    onAllow: () -> Unit,
    onDeny: () -> Unit,
    onNotNow: () -> Unit,
) {
    Box(Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
        ) {
            Text(heading, style = MaterialTheme.typography.headlineSmall)
            Text(
                body,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            SolventaButton(
                text = allow,
                style = SolventaButtonStyle.Filled,
                onClick = onAllow,
                modifier = Modifier.fillMaxWidth(),
            )
            SolventaButton(
                text = stringResource(R.string.claim_not_now),
                style = SolventaButtonStyle.Text,
                onClick = onNotNow,
                modifier = Modifier.fillMaxWidth(),
            )
        }
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(MaterialTheme.colorScheme.scrim.copy(alpha = 0.4f))
                .testTag("claim_permission_sheet"),
            contentAlignment = Alignment.Center,
        ) {
            Surface(
                shape = RoundedCornerShape(16.dp),
                color = MaterialTheme.colorScheme.surface,
                modifier = Modifier
                    .padding(horizontal = 28.dp)
                    .fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(start = 20.dp, top = 20.dp, end = 20.dp, bottom = 12.dp),
                    verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s8),
                ) {
                    Text(stringResource(R.string.claim_permission_app), style = MaterialTheme.typography.labelMedium)
                    Text(dialogTitle, style = MaterialTheme.typography.titleMedium)
                    Text(
                        dialogBody,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    SolventaButton(
                        text = primary,
                        style = SolventaButtonStyle.Filled,
                        onClick = onAllow,
                        modifier = Modifier.fillMaxWidth(),
                        testTag = "claim_permission_allow",
                    )
                    SolventaButton(
                        text = secondary,
                        style = SolventaButtonStyle.Filled,
                        onClick = onAllow,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    SolventaButton(
                        text = stringResource(R.string.claim_permission_deny),
                        style = SolventaButtonStyle.Text,
                        onClick = onDeny,
                        modifier = Modifier.fillMaxWidth(),
                        testTag = "claim_permission_deny",
                    )
                }
            }
        }
    }
}
