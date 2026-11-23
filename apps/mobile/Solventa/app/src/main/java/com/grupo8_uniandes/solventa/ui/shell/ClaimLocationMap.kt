package com.grupo8_uniandes.solventa.ui.shell

import android.content.Context
import android.os.Build
import android.view.MotionEvent
import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.viewinterop.AndroidView
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint as MapPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker

internal fun showClaimMap(): Boolean =
    !Build.FINGERPRINT.equals("robolectric", ignoreCase = true)

@Composable
internal fun ClaimLocationMap(point: GeoPoint, modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier.clipToBounds(),
        factory = { context ->
            FrameLayout(context).apply {
                clipChildren = true
                clipToPadding = true
                addView(
                    boundedMap(context, point),
                    FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT,
                    ),
                )
            }
        },
        update = { frame ->
            (frame.parent as? ViewGroup)?.apply {
                clipChildren = true
                clipToPadding = true
            }
            val map = frame.getChildAt(0) as MapView
            val target = MapPoint(point.lat, point.lng)
            map.controller.setCenter(target)
            map.overlays.filterIsInstance<Marker>().firstOrNull()?.position = target
            map.onResume()
        },
        onRelease = { frame ->
            (frame.getChildAt(0) as? MapView)?.onDetach()
        },
    )
}

private fun boundedMap(context: Context, point: GeoPoint): MapView {
    Configuration.getInstance().apply {
        userAgentValue = context.packageName
        load(context, context.getSharedPreferences("osmdroid", Context.MODE_PRIVATE))
    }
    val markerPoint = MapPoint(point.lat, point.lng)
    return BoundedMapView(context).apply {
        setTileSource(TileSourceFactory.MAPNIK)
        setMultiTouchControls(false)
        isHorizontalMapRepetitionEnabled = false
        isVerticalMapRepetitionEnabled = false
        controller.setZoom(16.0)
        controller.setCenter(markerPoint)
        overlays.add(
            Marker(this).apply {
                position = markerPoint
                setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
            },
        )
    }
}

/**
 * MapView calls requestLayout while tiles load. Inside a scrolling Compose column that
 * call detaches the view from its slot and draws it over the rest of the form.
 */
private class BoundedMapView(context: Context) : MapView(context) {
    private var layingOut = false

    override fun requestLayout() {
        if (layingOut) return
        super.requestLayout()
        post {
            if (width == 0 || height == 0 || layingOut) return@post
            layingOut = true
            measure(
                MeasureSpec.makeMeasureSpec(width, MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(height, MeasureSpec.EXACTLY),
            )
            layout(left, top, right, bottom)
            layingOut = false
        }
    }

    override fun dispatchTouchEvent(event: MotionEvent): Boolean = false
}
