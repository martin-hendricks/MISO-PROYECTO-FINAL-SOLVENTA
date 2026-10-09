package com.grupo8_uniandes.solventa.region

import android.app.Activity
import android.content.Context
import android.view.ContextThemeWrapper
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.ui.region.findActivity
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class FindActivityTest {
    @Test
    fun givenActivity_whenSearched_thenThatActivity() {
        val activity = Robolectric.buildActivity(Activity::class.java).setup().get()

        assertSame(activity, activity.findActivity())
    }

    @Test
    fun givenWrapperAroundActivity_whenSearched_thenInnerActivity() {
        val activity = Robolectric.buildActivity(Activity::class.java).setup().get()
        val wrapped = ContextThemeWrapper(activity, android.R.style.Theme_DeviceDefault)

        assertSame(activity, wrapped.findActivity())
    }

    @Test
    fun givenApplicationContext_whenSearched_thenNull() {
        val context = ApplicationProvider.getApplicationContext<Context>()

        assertNull(context.findActivity())
    }
}
