package com.grupo8_uniandes.solventa.shell

import android.content.Context
import android.content.Intent
import android.os.Looper
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.domain.push.PushTarget
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class MainActivityPushIntentTest {
    @Test
    fun givenPushExtras_whenCreatedAndReceivingANewIntent_thenTheyAreReadAndRemoved() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val intent = Intent(context, MainActivity::class.java).apply {
            putExtra(MainActivity.EXTRA_ENTER_SIGNED_IN_SHELL, true)
            putExtra(MainActivity.EXTRA_PUSH_DESTINO, "poliza-detalle")
            putExtra(MainActivity.EXTRA_PUSH_POLIZA, "POL-2026-00000002")
        }
        val controller = Robolectric.buildActivity(MainActivity::class.java, intent).setup()
        shadowOf(Looper.getMainLooper()).idle()
        val activity = controller.get()

        assertEquals(PushTarget.PolizaDetalle("POL-2026-00000002"), activity.deliveredPush)
        assertFalse(activity.intent.hasExtra(MainActivity.EXTRA_PUSH_DESTINO))
        assertFalse(activity.intent.hasExtra(MainActivity.EXTRA_PUSH_POLIZA))

        controller.newIntent(
            Intent(context, MainActivity::class.java).apply {
                putExtra(MainActivity.EXTRA_ENTER_SIGNED_IN_SHELL, true)
                putExtra(MainActivity.EXTRA_PUSH_DESTINO, "inicio")
            },
        )
        shadowOf(Looper.getMainLooper()).idle()
        assertEquals(PushTarget.Inicio, activity.deliveredPush)
        assertFalse(activity.intent.hasExtra(MainActivity.EXTRA_PUSH_DESTINO))
        assertFalse(activity.intent.hasExtra(MainActivity.EXTRA_PUSH_POLIZA))

        val rotated = controller.recreate()
        shadowOf(Looper.getMainLooper()).idle()
        val again = rotated.get()
        assertNull(again.deliveredPush)
        assertNull(again.pendingPush)
        assertFalse(again.intent.hasExtra(MainActivity.EXTRA_PUSH_DESTINO))
        assertFalse(again.intent.hasExtra(MainActivity.EXTRA_PUSH_POLIZA))
    }
}
