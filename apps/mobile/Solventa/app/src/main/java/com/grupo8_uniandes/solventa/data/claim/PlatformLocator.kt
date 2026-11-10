package com.grupo8_uniandes.solventa.data.claim

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.location.LocationManager
import android.os.CancellationSignal
import androidx.core.location.LocationManagerCompat
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

class PlatformLocator(
    private val context: Context,
    private val timeoutMs: Long = 8_000,
) : DeviceLocator {
    @SuppressLint("MissingPermission")
    override suspend fun current(): GeoPoint? = withContext(Dispatchers.IO) {
        val manager = context.getSystemService(LocationManager::class.java) ?: return@withContext null
        val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
        for (provider in providers) {
            val enabled = runCatching { manager.isProviderEnabled(provider) }.getOrDefault(false)
            if (!enabled) continue
            val location = readCurrent(manager, provider) ?: lastKnown(manager, provider)
            if (location != null) return@withContext location.toPoint()
        }
        null
    }

    @SuppressLint("MissingPermission")
    private suspend fun readCurrent(manager: LocationManager, provider: String): Location? =
        withTimeoutOrNull(timeoutMs) {
            suspendCancellableCoroutine { cont ->
                val signal = CancellationSignal()
                cont.invokeOnCancellation { signal.cancel() }
                try {
                    LocationManagerCompat.getCurrentLocation(
                        manager,
                        provider,
                        signal,
                        Runnable::run,
                    ) { location ->
                        if (cont.isActive) cont.resume(location)
                    }
                } catch (_: Throwable) {
                    if (cont.isActive) cont.resume(null)
                }
            }
        }

    @SuppressLint("MissingPermission")
    private fun lastKnown(manager: LocationManager, provider: String): Location? =
        runCatching { manager.getLastKnownLocation(provider) }.getOrNull()
}

private fun Location.toPoint() = GeoPoint(
    lat = latitude,
    lng = longitude,
    precisionM = if (hasAccuracy()) accuracy.toInt() else 0,
)
