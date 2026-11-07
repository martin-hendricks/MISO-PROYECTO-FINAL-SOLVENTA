package com.grupo8_uniandes.solventa.ui.shell

import android.content.Intent
import android.net.Uri
import android.provider.Settings
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
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNoticeDraft
import com.grupo8_uniandes.solventa.ui.capture.EvidencePickers
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun EvidenciaAvisoScreen(
    draft: ClaimNoticeDraft,
    onAttach: (Attachment, ByteArray) -> Unit,
    onRemove: (String) -> Unit,
    onCameraDenied: () -> Unit,
    onSend: () -> Unit,
    onQueue: () -> Unit,
    sending: Boolean = false,
    queued: Boolean = false,
    rejection: String? = null,
    fileRejected: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    SideEffect {
        AvisoChrome.titleRes = R.string.claim_evidence_title
        AvisoChrome.coverTabs = false
    }
    DisposableEffect(Unit) {
        onDispose { AvisoChrome.reset() }
    }
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = SolventaSpacing.gutter, vertical = SolventaSpacing.s12)
            .testTag("screen_evidencia_aviso"),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.claim_evidence_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        if (draft.cameraDenied) {
            Text(
                text = stringResource(R.string.claim_camera_denied),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.testTag("claim_camera_denied"),
            )
            Text(
                text = stringResource(R.string.claim_camera_denied_help),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            SolventaButton(
                text = stringResource(R.string.claim_settings),
                style = SolventaButtonStyle.Tonal,
                onClick = {
                    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                        data = Uri.fromParts("package", context.packageName, null)
                    }
                    context.startActivity(intent)
                },
                modifier = Modifier.fillMaxWidth(),
                testTag = "claim_settings",
            )
        }
        EvidenceGallery(files = draft.adjuntos, onRemove = onRemove)
        EvidencePickers(
            onPicked = onAttach,
            onCameraDenied = onCameraDenied,
        )
        if (queued) {
            Text(
                text = stringResource(R.string.claim_queued),
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.testTag("claim_queued"),
            )
        }
        if (fileRejected) {
            Text(
                text = stringResource(R.string.claim_file_rejected),
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.testTag("claim_file_rejected"),
            )
        }
        rejection?.let { message ->
            Text(text = message, style = MaterialTheme.typography.bodyMedium)
        }
        SolventaButton(
            text = stringResource(R.string.claim_evidence_send),
            style = SolventaButtonStyle.Filled,
            onClick = onSend,
            enabled = draft.adjuntos.isNotEmpty() && !sending,
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_send",
        )
        SolventaButton(
            text = stringResource(R.string.claim_evidence_queue),
            style = SolventaButtonStyle.Tonal,
            onClick = onQueue,
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_queue",
        )
    }
}
