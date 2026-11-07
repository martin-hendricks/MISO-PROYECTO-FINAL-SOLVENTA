package com.grupo8_uniandes.solventa.ui.capture

import android.Manifest
import android.content.ContentResolver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.core.content.ContextCompat
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import java.io.File
import java.util.UUID

private const val VIDEO_LIMIT_SECONDS = 30
private const val VIDEO_LIMIT_BYTES = 10L * 1024 * 1024

data class PickedEvidence(
    val attachment: Attachment,
    val bytes: ByteArray,
)

class LimitedCaptureVideo : ActivityResultContracts.CaptureVideo() {
    override fun createIntent(context: Context, input: Uri): Intent {
        return super.createIntent(context, input).apply {
            putExtra(android.provider.MediaStore.EXTRA_DURATION_LIMIT, VIDEO_LIMIT_SECONDS)
            putExtra(android.provider.MediaStore.EXTRA_SIZE_LIMIT, VIDEO_LIMIT_BYTES)
        }
    }
}

fun readPicked(resolver: ContentResolver, uri: Uri): PickedEvidence? {
    val bytes = resolver.openInputStream(uri)?.use { it.readBytes() }?.takeIf { it.isNotEmpty() } ?: return null
    var name = uri.lastPathSegment?.substringAfterLast('/')?.ifBlank { null } ?: "evidencia"
    var size = bytes.size.toLong()
    runCatching {
        resolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE), null, null, null)
    }.getOrNull()?.use { cursor ->
        if (cursor.moveToFirst()) {
            val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
            if (nameIndex >= 0) cursor.getString(nameIndex)?.takeIf { it.isNotBlank() }?.let { name = it }
            if (sizeIndex >= 0 && !cursor.isNull(sizeIndex)) size = cursor.getLong(sizeIndex)
        }
    }
    val mime = evidenceMime(resolver.getType(uri), name)
    val kind = evidenceKind(mime) ?: AttachmentKind.SOPORTE
    return PickedEvidence(
        attachment = Attachment(
            tipo = kind,
            nombre = name,
            contentType = mime,
            tamanoBytes = size.coerceAtLeast(bytes.size.toLong()),
        ),
        bytes = bytes,
    )
}

internal fun evidenceMime(reported: String?, name: String): String {
    val raw = reported ?: android.webkit.MimeTypeMap.getSingleton()
        .getMimeTypeFromExtension(name.substringAfterLast('.', ""))
        ?: "application/octet-stream"
    return if (raw == "image/jpg" || raw == "image/pjpeg") "image/jpeg" else raw
}

internal fun evidenceKind(mime: String): AttachmentKind? = when {
    mime.startsWith("image/") -> AttachmentKind.FOTO
    mime.startsWith("video/") -> AttachmentKind.VIDEO
    mime == "application/pdf" -> AttachmentKind.RECIBO
    else -> null
}

private enum class CaptureKind { Photo, Video }

@Composable
fun EvidencePickers(
    onPicked: (Attachment, ByteArray) -> Unit,
    onCameraDenied: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    var pending by remember { mutableStateOf<CaptureKind?>(null) }
    var pendingFile by remember { mutableStateOf<File?>(null) }
    var pendingUri by remember { mutableStateOf<Uri?>(null) }
    val takePicture = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        deliver(context, success, pendingFile, pendingUri, onPicked)
    }
    val captureVideo = rememberLauncherForActivityResult(LimitedCaptureVideo()) { success ->
        deliver(context, success, pendingFile, pendingUri, onPicked)
    }
    val pickFile = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            readPicked(context.contentResolver, uri)?.let { onPicked(it.attachment, it.bytes) }
        }
    }
    fun launch(kind: CaptureKind) {
        val file = claimFile(context, kind)
        val uri = captureUri(context, file)
        pending = kind
        pendingFile = file
        pendingUri = uri
        when (kind) {
            CaptureKind.Photo -> takePicture.launch(uri)
            CaptureKind.Video -> captureVideo.launch(uri)
        }
    }
    val requestCamera = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        val kind = pending
        if (granted && kind != null) {
            launch(kind)
        } else {
            pending = null
            onCameraDenied()
        }
    }
    fun start(kind: CaptureKind) {
        val granted = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.CAMERA,
        ) == PackageManager.PERMISSION_GRANTED
        if (granted) {
            launch(kind)
        } else {
            pending = kind
            requestCamera.launch(Manifest.permission.CAMERA)
        }
    }
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        SolventaButton(
            text = stringResource(R.string.claim_take_photo),
            style = SolventaButtonStyle.Tonal,
            onClick = { start(CaptureKind.Photo) },
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_take_photo",
        )
        SolventaButton(
            text = stringResource(R.string.claim_record_video),
            style = SolventaButtonStyle.Tonal,
            onClick = { start(CaptureKind.Video) },
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_record_video",
        )
        SolventaButton(
            text = stringResource(R.string.claim_pick_file),
            style = SolventaButtonStyle.Tonal,
            onClick = { pickFile.launch(arrayOf("image/*", "video/*", "application/pdf")) },
            modifier = Modifier.fillMaxWidth(),
            testTag = "claim_pick_file",
        )
    }
}

private fun deliver(
    context: Context,
    success: Boolean,
    file: File?,
    uri: Uri?,
    onPicked: (Attachment, ByteArray) -> Unit,
) {
    if (!success) return
    val picked = uri?.let { readPicked(context.contentResolver, it) } ?: file?.let(::readFile)
    picked?.let { onPicked(it.attachment, it.bytes) }
}

internal fun readFile(file: File): PickedEvidence? {
    if (!file.isFile || file.length() == 0L) return null
    val bytes = file.readBytes()
    val mime = evidenceMime(null, file.name)
    val kind = evidenceKind(mime) ?: AttachmentKind.SOPORTE
    return PickedEvidence(
        attachment = Attachment(kind, file.name, mime, bytes.size.toLong()),
        bytes = bytes,
    )
}

private fun claimFile(context: Context, kind: CaptureKind): File {
    val name = when (kind) {
        CaptureKind.Photo -> "foto-${UUID.randomUUID()}.jpg"
        CaptureKind.Video -> "video-${UUID.randomUUID()}.mp4"
    }
    return File(context.cacheDir, "claim/$name")
}
