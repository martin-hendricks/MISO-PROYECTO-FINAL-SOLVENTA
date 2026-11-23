package com.grupo8_uniandes.solventa.ui.capture

import android.content.Context
import android.net.Uri
import androidx.core.content.FileProvider
import java.io.File

internal fun captureUri(context: Context, file: File): Uri {
    prepareCaptureFile(file)
    return FileProvider.getUriForFile(
        context,
        "${context.packageName}.fileprovider",
        file,
    )
}

internal fun prepareCaptureFile(file: File) {
    file.parentFile?.mkdirs()
    if (!file.exists()) file.createNewFile()
}
