package com.grupo8_uniandes.solventa.push

import android.content.Context
import android.util.Log
import com.google.android.gms.tasks.Task
import com.google.firebase.FirebaseApp
import com.google.firebase.installations.FirebaseInstallations
import com.google.firebase.messaging.FirebaseMessaging
import com.grupo8_uniandes.solventa.domain.push.PushToken
import kotlin.coroutines.resume
import kotlinx.coroutines.suspendCancellableCoroutine

class FirebasePushToken(
    private val context: Context,
) : PushToken {
    override suspend fun current(): String? {
        if (FirebaseApp.getApps(context).isEmpty()) return null
        val fid = await(FirebaseInstallations.getInstance().id)
        if (fid != null) Log.i(TAG, "FID $fid")
        return fid
    }

    override suspend fun link(): String? {
        if (FirebaseApp.getApps(context).isEmpty()) return null
        val registrado = awaitUnit(FirebaseMessaging.getInstance().register())
        if (!registrado) return null
        return current()
    }
}

fun logRegistration(context: Context) {
    if (FirebaseApp.getApps(context).isEmpty()) {
        Log.w(TAG, "Firebase no está inicializado")
        return
    }
    FirebaseMessaging.getInstance().register().addOnFailureListener { error ->
        Log.e(TAG, "Registro FCM falló", error)
    }
}

class NoPushToken : PushToken {
    override suspend fun current(): String? = null
}

private const val TAG = "SolventaFid"

private suspend fun await(task: Task<String>): String? = suspendCancellableCoroutine { continuation ->
    task.addOnCompleteListener { finished ->
        if (!continuation.isActive) return@addOnCompleteListener
        val value = if (finished.isSuccessful) finished.result else null
        continuation.resume(value?.takeIf { it.isNotBlank() })
    }
}

private suspend fun awaitUnit(task: Task<Void>): Boolean = suspendCancellableCoroutine { continuation ->
    task.addOnCompleteListener { finished ->
        if (!continuation.isActive) return@addOnCompleteListener
        continuation.resume(finished.isSuccessful)
    }
}
