package com.grupo8_uniandes.solventa.ui.shell

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Image
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.EvidenceBytes
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing
import java.io.File

private val thumbShape = RoundedCornerShape(8.dp)
private const val evidenceLimit = 5

@Composable
internal fun EvidenceGallery(
    files: List<Attachment>,
    onRemove: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    if (files.isEmpty()) {
        Box(
            modifier = modifier
                .fillMaxWidth()
                .height(120.dp)
                .clip(thumbShape)
                .background(MaterialTheme.colorScheme.surfaceContainerHighest)
                .testTag("claim_evidence_preview"),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = stringResource(R.string.claim_evidence_empty),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        return
    }
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s12),
    ) {
        Text(
            text = stringResource(R.string.claim_evidence_count, files.size.coerceAtMost(evidenceLimit)),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.testTag("claim_evidence_count"),
        )
        files.forEachIndexed { index, file ->
            EvidenceCard(
                file = file,
                featured = index == 0,
                onRemove = { onRemove(file.nombre) },
            )
        }
    }
}

@Composable
private fun EvidenceCard(
    file: Attachment,
    featured: Boolean,
    onRemove: () -> Unit,
) {
    val context = LocalContext.current
    val frame = remember(file.nombre, file.contentType) {
        evidenceFrame(EvidenceBytes.read(file.nombre), file.contentType, context.cacheDir)
    }
    Column(verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s8)) {
        val preview = frame
        if (preview != null) {
            Image(
                bitmap = preview.asImageBitmap(),
                contentDescription = file.nombre,
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(if (featured) 180.dp else 96.dp)
                    .clip(thumbShape)
                    .testTag(if (featured) "claim_evidence_preview" else "claim_thumb_${file.nombre}"),
            )
        } else {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(if (featured) 96.dp else 72.dp)
                    .clip(thumbShape)
                    .background(MaterialTheme.colorScheme.surfaceContainerHighest)
                    .testTag(if (featured) "claim_evidence_preview" else "claim_thumb_${file.nombre}"),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = file.placeholderIcon(),
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(32.dp),
                )
            }
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .testTag("claim_file_${file.nombre}"),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Column(Modifier.weight(1f)) {
                Text(text = file.nombre, style = MaterialTheme.typography.bodyMedium)
                Text(
                    text = "${file.contentType} · ${file.tamanoBytes}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            SolventaButton(
                text = stringResource(R.string.claim_remove),
                style = SolventaButtonStyle.Text,
                onClick = onRemove,
                testTag = "claim_remove_${file.nombre}",
            )
        }
    }
}

private fun Attachment.placeholderIcon(): ImageVector = when {
    contentType.startsWith("video/") -> Icons.Filled.Videocam
    contentType == "application/pdf" -> Icons.Filled.PictureAsPdf
    else -> Icons.Filled.Image
}

internal fun evidenceFrame(bytes: ByteArray?, contentType: String, cacheDir: File): Bitmap? {
    if (bytes == null || bytes.isEmpty()) return null
    if (contentType.startsWith("image/")) {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
        val options = BitmapFactory.Options().apply {
            inSampleSize = sampleSize(bounds.outWidth, bounds.outHeight)
        }
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.size, options)
    }
    if (!contentType.startsWith("video/")) return null
    val file = File(cacheDir, "claim-thumb.mp4")
    return runCatching {
        file.writeBytes(bytes)
        val retriever = MediaMetadataRetriever()
        try {
            retriever.setDataSource(file.absolutePath)
            retriever.getFrameAtTime(0)
        } finally {
            retriever.release()
        }
    }.getOrNull()
}

private fun sampleSize(width: Int, height: Int): Int {
    var size = 1
    while (width / size > 720 || height / size > 720) size *= 2
    return size
}
