package com.grupo8_uniandes.solventa.ui.registration

import android.graphics.Bitmap
import android.graphics.Matrix
import android.view.View
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import java.io.ByteArrayOutputStream
import java.util.concurrent.Executor

/**
 * Binds the front camera and keeps the JPEG in memory. The phases and outcomes
 * live in [LivenessViewModel], so this file has no branching the unit suite can reach.
 */
@Composable
fun FrontCameraPreview(
    captureTicket: Int,
    onPhoto: (ByteArray) -> Unit,
    onUnavailable: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val capture = remember {
        ImageCapture.Builder()
            .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
            .build()
    }
    val executor = remember(context) { ContextCompat.getMainExecutor(context) }
    val previewView = remember(context) {
        PreviewView(context).apply {
            scaleType = PreviewView.ScaleType.FILL_CENTER
        }
    }

    DisposableEffect(lifecycleOwner, previewView) {
        val future = ProcessCameraProvider.getInstance(context)
        val listener = Runnable {
            val provider = try {
                future.get()
            } catch (_: Exception) {
                onUnavailable()
                return@Runnable
            }
            val front = CameraSelector.DEFAULT_FRONT_CAMERA
            if (!provider.hasCamera(front)) {
                onUnavailable()
                return@Runnable
            }
            val preview = Preview.Builder().build().also {
                it.surfaceProvider = previewView.surfaceProvider
            }
            previewView.display?.rotation?.let { rotation ->
                preview.targetRotation = rotation
                capture.targetRotation = rotation
            }
            try {
                provider.unbindAll()
                provider.bindToLifecycle(lifecycleOwner, front, preview, capture)
            } catch (_: Exception) {
                onUnavailable()
            }
        }
        val layoutListener = View.OnLayoutChangeListener { view, _, _, _, _, _, _, _, _ ->
            val rotation = view.display?.rotation ?: return@OnLayoutChangeListener
            capture.targetRotation = rotation
        }
        previewView.addOnLayoutChangeListener(layoutListener)
        future.addListener(listener, executor)
        onDispose {
            previewView.removeOnLayoutChangeListener(layoutListener)
            if (future.isDone) {
                runCatching { future.get().unbindAll() }
            }
        }
    }

    DisposableEffect(captureTicket) {
        if (captureTicket > 0) {
            takeJpeg(capture, executor, onPhoto)
        }
        onDispose { }
    }

    AndroidView(factory = { previewView }, modifier = modifier)
}

private fun takeJpeg(capture: ImageCapture, executor: Executor, onPhoto: (ByteArray) -> Unit) {
    capture.takePicture(
        executor,
        object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(image: ImageProxy) {
                val bytes = jpegUpright(image)
                image.close()
                onPhoto(bytes)
            }

            override fun onError(exception: ImageCaptureException) = Unit
        },
    )
}

private fun jpegUpright(image: ImageProxy): ByteArray {
    val decoded = image.toBitmap()
    val degrees = image.imageInfo.rotationDegrees
    val upright = if (degrees % 360 == 0) {
        decoded
    } else {
        Bitmap.createBitmap(
            decoded,
            0,
            0,
            decoded.width,
            decoded.height,
            Matrix().apply { postRotate(degrees.toFloat()) },
            true,
        )
    }
    val encoded = ByteArrayOutputStream().use { stream ->
        upright.compress(Bitmap.CompressFormat.JPEG, 92, stream)
        stream.toByteArray()
    }
    if (upright != decoded) decoded.recycle()
    upright.recycle()
    return encoded
}
