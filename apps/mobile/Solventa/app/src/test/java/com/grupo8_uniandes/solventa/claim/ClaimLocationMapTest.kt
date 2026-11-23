package com.grupo8_uniandes.solventa.claim

import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.dp
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.ui.shell.ClaimLocationMap
import com.grupo8_uniandes.solventa.ui.shell.showClaimMap
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.osmdroid.views.MapView
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowBuild
import org.robolectric.shadows.ShadowLooper

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h800dp")
class ClaimLocationMapTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenAPoint_whenTheMapIsShown_thenItCentersAndIgnoresTouches() {
        ShadowBuild.setFingerprint("google/sdk_gphone64_arm64")
        assertTrue(showClaimMap())
        val point = mutableStateOf(GeoPoint(4.65, -74.05, 12))
        rule.setContent {
            ClaimLocationMap(
                point = point.value,
                modifier = Modifier.size(width = 200.dp, height = 180.dp),
            )
        }
        val map = rule.activity.window.decorView.findMap()
        assertNotNull(map)
        map!!.requestLayout()
        ShadowLooper.idleMainLooper()
        map.measure(
            View.MeasureSpec.makeMeasureSpec(400, View.MeasureSpec.EXACTLY),
            View.MeasureSpec.makeMeasureSpec(360, View.MeasureSpec.EXACTLY),
        )
        map.layout(0, 0, 400, 360)
        val event = MotionEvent.obtain(0, 0, MotionEvent.ACTION_DOWN, 10f, 10f, 0)
        assertFalse(map.dispatchTouchEvent(event))
        event.recycle()
        val layingOut = map.javaClass.getDeclaredField("layingOut")
        layingOut.isAccessible = true
        layingOut.setBoolean(map, true)
        map.requestLayout()
        layingOut.setBoolean(map, false)
        map.requestLayout()
        ShadowLooper.idleMainLooper()
        map.overlays.clear()
        point.value = GeoPoint(6.2, -75.57, 8)
        rule.waitForIdle()
    }

    @Test
    fun givenNoModifier_whenTheMapLeaves_thenTheViewIsDetached() {
        rule.setContent {
            ClaimLocationMap(point = GeoPoint(4.65, -74.05, 12))
        }
        assertNotNull(rule.activity.window.decorView.findMap())
        rule.activity.finish()
        ShadowLooper.idleMainLooper()
    }

    @Test
    fun givenRobolectric_whenAsked_thenTheEmbeddedMapStaysOff() {
        ShadowBuild.setFingerprint("robolectric")
        assertFalse(showClaimMap())
    }
}

private fun View.findMap(): MapView? {
    if (this is MapView) return this
    if (this is ViewGroup) {
        for (index in 0 until childCount) {
            getChildAt(index).findMap()?.let { return it }
        }
    }
    return null
}
