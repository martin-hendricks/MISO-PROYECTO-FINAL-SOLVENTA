package com.grupo8_uniandes.solventa.data.profile

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat
import com.grupo8_uniandes.solventa.domain.profile.DevicePermissionReader
import com.grupo8_uniandes.solventa.domain.profile.PermissionKind
import com.grupo8_uniandes.solventa.domain.profile.PermissionRow

class AndroidDevicePermissionReader(
    private val context: Context,
) : DevicePermissionReader {
    override fun read(): List<PermissionRow> = listOf(
        PermissionRow(
            PermissionKind.Location,
            granted(Manifest.permission.ACCESS_FINE_LOCATION) ||
                granted(Manifest.permission.ACCESS_COARSE_LOCATION),
        ),
        PermissionRow(PermissionKind.Camera, granted(Manifest.permission.CAMERA)),
        PermissionRow(PermissionKind.Photos, granted(photosPermission())),
    )

    private fun photosPermission(): String =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            Manifest.permission.READ_MEDIA_IMAGES
        } else {
            Manifest.permission.READ_EXTERNAL_STORAGE
        }

    private fun granted(permission: String): Boolean =
        ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
}
