package com.grupo8_uniandes.solventa.push

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.grupo8_uniandes.solventa.domain.profile.SessionRepository
import com.grupo8_uniandes.solventa.domain.push.PushOptIn
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.koin.core.context.GlobalContext

class SolventaMessagingService : FirebaseMessagingService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onRegistered(installationId: String) {
        Log.i(TAG, "FID $installationId")
        val koin = GlobalContext.getOrNull() ?: return
        if (!koin.get<SessionRepository>().isOpen()) return
        val optIn = koin.get<PushOptIn>()
        scope.launch { optIn.onNewToken(installationId) }
    }

    private companion object {
        const val TAG = "SolventaFid"
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val aviso = message.notification
        Log.i(TAG, "mensaje titulo=${aviso?.title} data=${message.data}")
        val datos = message.data.toMutableMap()
        if (datos["titulo"].isNullOrBlank()) datos["titulo"] = aviso?.title.orEmpty()
        if (datos["cuerpo"].isNullOrBlank()) datos["cuerpo"] = aviso?.body.orEmpty()
        PushNotificationBuilder.show(this, datos)
    }
}
