package com.grupo8_uniandes.solventa.ui.shell

import android.graphics.Bitmap
import com.grupo8_uniandes.solventa.ui.capture.decodeOrientedImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

private val thumbClient: OkHttpClient by lazy {
    OkHttpClient.Builder()
        .callTimeout(8, TimeUnit.SECONDS)
        .build()
}

internal suspend fun fetchEvidenceThumb(url: String): Bitmap? {
    if (!url.startsWith("https://") && !url.startsWith("http://")) return null
    return withContext(Dispatchers.IO) {
        runCatching {
            thumbClient.newCall(Request.Builder().url(url).build()).execute().use { response ->
                if (!response.isSuccessful) return@runCatching null
                val bytes = response.body?.bytes()?.takeIf { it.isNotEmpty() } ?: return@runCatching null
                decodeOrientedImage(bytes)
            }
        }.getOrNull()
    }
}
