package com.grupo8_uniandes.solventa.ui.capture

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream

internal fun normalizeJpegOrientation(bytes: ByteArray): ByteArray {
    if (!jpegOrientation(bytes).needsRotation()) return bytes
    val decoded = BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: return bytes
    val upright = rotate(decoded, jpegOrientation(bytes)) ?: return bytes
    val out = ByteArrayOutputStream()
    if (!upright.compress(Bitmap.CompressFormat.JPEG, 92, out)) return bytes
    return out.toByteArray()
}

internal fun decodeOrientedImage(bytes: ByteArray): Bitmap? {
    val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
    if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null
    val options = BitmapFactory.Options().apply {
        inSampleSize = evidenceSampleSize(bounds.outWidth, bounds.outHeight)
    }
    val decoded = BitmapFactory.decodeByteArray(bytes, 0, bytes.size, options) ?: return null
    val orientation = jpegOrientation(bytes)
    if (!orientation.needsRotation()) return decoded
    return rotate(decoded, orientation) ?: decoded
}

private fun evidenceSampleSize(width: Int, height: Int): Int {
    var size = 1
    while (width / size > 720 || height / size > 720) size *= 2
    return size
}

private fun jpegOrientation(bytes: ByteArray): Int = try {
    ExifInterface(ByteArrayInputStream(bytes)).getAttributeInt(
        ExifInterface.TAG_ORIENTATION,
        ExifInterface.ORIENTATION_NORMAL,
    )
} catch (_: Throwable) {
    ExifInterface.ORIENTATION_NORMAL
}

private fun Int.needsRotation(): Boolean = when (this) {
    ExifInterface.ORIENTATION_ROTATE_90,
    ExifInterface.ORIENTATION_ROTATE_180,
    ExifInterface.ORIENTATION_ROTATE_270,
    -> true
    else -> false
}

private fun rotate(bitmap: Bitmap, orientation: Int): Bitmap? {
    val degrees = when (orientation) {
        ExifInterface.ORIENTATION_ROTATE_90 -> 90f
        ExifInterface.ORIENTATION_ROTATE_180 -> 180f
        ExifInterface.ORIENTATION_ROTATE_270 -> 270f
        else -> return bitmap
    }
    val matrix = Matrix().apply { postRotate(degrees) }
    return runCatching {
        Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }.getOrNull()
}
