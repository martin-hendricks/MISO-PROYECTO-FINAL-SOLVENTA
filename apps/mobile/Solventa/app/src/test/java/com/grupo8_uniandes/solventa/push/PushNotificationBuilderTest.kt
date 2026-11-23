package com.grupo8_uniandes.solventa.push

import android.Manifest
import android.app.Application
import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.MainActivity
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
class PushNotificationBuilderTest {
    @Test
    fun givenADataMessage_whenShown_thenTheChannelTitleAndExtrasMatch() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        shadowOf(context as Application).grantPermissions(Manifest.permission.POST_NOTIFICATIONS)
        val id = "6f1c0a2e-1b4d-4e3a-9c77-0a1b2c3d4e5f"
        PushNotificationBuilder.show(
            context,
            mapOf(
                "notificacionId" to id,
                "titulo" to "Tu póliza fue renovada",
                "cuerpo" to "La póliza POL-2026-00000002 ahora vence el 2027-03-12.",
                "destino" to "poliza-detalle",
                "poliza" to "POL-2026-00000002",
            ),
        )

        val manager = context.getSystemService(NotificationManager::class.java)
        val channel = manager.getNotificationChannel(PushNotificationBuilder.CHANNEL_ID)
        assertEquals("Avisos de póliza", channel.name.toString())
        val posted = manager.activeNotifications.single()
        assertEquals(id.hashCode(), posted.id)
        val notification = posted.notification
        assertEquals(PushNotificationBuilder.CHANNEL_ID, notification.channelId)
        assertEquals("Tu póliza fue renovada", notification.extras.getString(Notification.EXTRA_TITLE))
        assertEquals(
            "La póliza POL-2026-00000002 ahora vence el 2027-03-12.",
            notification.extras.getString(Notification.EXTRA_TEXT),
        )
        assertTrue(notification.flags and Notification.FLAG_AUTO_CANCEL != 0)
        val pending = shadowOf(notification.contentIntent)
        assertEquals(id.hashCode(), pending.requestCode)
        assertTrue(pending.flags and PendingIntent.FLAG_IMMUTABLE != 0)
        assertEquals("poliza-detalle", pending.savedIntent.getStringExtra(MainActivity.EXTRA_PUSH_DESTINO))
        assertEquals("POL-2026-00000002", pending.savedIntent.getStringExtra(MainActivity.EXTRA_PUSH_POLIZA))
    }
}
