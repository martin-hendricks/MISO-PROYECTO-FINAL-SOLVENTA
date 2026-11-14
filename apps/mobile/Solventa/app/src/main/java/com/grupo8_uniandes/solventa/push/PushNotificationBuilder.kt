package com.grupo8_uniandes.solventa.push

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.R

object PushNotificationBuilder {
    const val CHANNEL_ID = "avisos_poliza_alta"

    fun ensureChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = context.getSystemService(NotificationManager::class.java) ?: return
        val existing = manager.getNotificationChannel(CHANNEL_ID)
        if (existing != null && existing.importance < NotificationManager.IMPORTANCE_HIGH) {
            manager.deleteNotificationChannel(CHANNEL_ID)
        }
        val channel = NotificationChannel(
            CHANNEL_ID,
            context.getString(R.string.push_channel_name),
            NotificationManager.IMPORTANCE_HIGH,
        )
        channel.description = context.getString(R.string.push_channel_description)
        manager.createNotificationChannel(channel)
    }

    fun show(context: Context, data: Map<String, String>) {
        val titulo = data["titulo"]?.takeIf { it.isNotBlank() } ?: return
        val cuerpo = data["cuerpo"]?.takeIf { it.isNotBlank() } ?: return
        ensureChannel(context)
        val notificationId = data["notificacionId"].orEmpty()
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra(MainActivity.EXTRA_PUSH_DESTINO, data["destino"])
            if (data.containsKey("poliza")) {
                putExtra(MainActivity.EXTRA_PUSH_POLIZA, data["poliza"])
            }
        }
        val pending = PendingIntent.getActivity(
            context,
            notificationId.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.info)
            .setContentTitle(titulo)
            .setContentText(cuerpo)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pending)
            .build()
        NotificationManagerCompat.from(context).notify(notificationId.hashCode(), notification)
    }
}
