package com.grupo8_uniandes.solventa.ui.shell

import android.content.Context
import android.content.res.Resources
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Typeface
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.model.BitmapDescriptor
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.Marker
import com.google.android.gms.maps.model.MarkerOptions
import com.google.maps.android.clustering.Cluster
import com.google.maps.android.clustering.ClusterManager
import com.google.maps.android.clustering.view.DefaultClusterRenderer
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderType
import com.grupo8_uniandes.solventa.prestadores.ProviderStack

internal const val GROUP_COLOR = 0xFF006A6A.toInt()

internal fun providerTypeColor(tipo: ProviderType): Int = when (tipo) {
    ProviderType.SERVICIO_TECNICO -> 0xFF1565C0
    ProviderType.TALLER_MOTOS -> 0xFFEF6C00
    ProviderType.IPS_URGENCIAS -> 0xFFC62828
    ProviderType.GRUA -> 0xFF6A1B9A
    ProviderType.ASISTENCIA_VIAJERO -> 0xFF00838F
    ProviderType.PUNTO_AEROPUERTO -> 0xFF283593
    ProviderType.IPS_EXAMENES -> 0xFFAD1457
    ProviderType.FUNERARIA -> 0xFF455A64
    ProviderType.CENTRO_ATENCION -> 0xFF2E7D32
}.toInt()

internal fun clusterTier(count: Int): Int = when {
    count < 10 -> 0
    count < 50 -> 1
    else -> 2
}

internal fun clusterLabel(resources: Resources, count: Int): String =
    resources.getQuantityString(R.plurals.providers_cluster_a11y, count, count)

internal fun markerLabel(resources: Resources, stack: ProviderStack): String =
    stack.providers.joinToString(", ") { providerLabel(resources, it) }

private fun providerLabel(resources: Resources, provider: Provider): String =
    resources.getString(R.string.providers_marker_a11y, provider.nombre, resources.getString(providerTypeLabel(provider.tipo)))

internal class ProviderClusterRenderer(
    private val context: Context,
    map: GoogleMap,
    manager: ClusterManager<ProviderStack>,
) : DefaultClusterRenderer<ProviderStack>(context, map, manager) {
    private val density = context.resources.displayMetrics.density
    private val icons = mutableMapOf<String, BitmapDescriptor>()

    init {
        minClusterSize = 2
    }

    override fun onBeforeClusterRendered(cluster: Cluster<ProviderStack>, markerOptions: MarkerOptions) {
        val count = cluster.count()
        markerOptions
            .icon(groupIcon(count))
            .contentDescription(clusterLabel(context.resources, count))
            .anchor(0.5f, 0.5f)
    }

    override fun onClusterUpdated(cluster: Cluster<ProviderStack>, marker: Marker) {
        marker.setIcon(groupIcon(cluster.count()))
    }

    override fun onBeforeClusterItemRendered(item: ProviderStack, markerOptions: MarkerOptions) {
        markerOptions
            .icon(itemIcon(item))
            .title(markerLabel(context.resources, item))
            .contentDescription(markerLabel(context.resources, item))
            .zIndex(item.zIndex)
            .anchor(0.5f, 0.5f)
    }

    override fun onClusterItemUpdated(item: ProviderStack, marker: Marker) {
        marker.setIcon(itemIcon(item))
        marker.title = markerLabel(context.resources, item)
        marker.zIndex = item.zIndex
    }

    private fun Cluster<ProviderStack>.count(): Int = items.sumOf { it.providers.size }

    private fun groupIcon(count: Int): BitmapDescriptor {
        val size = when (clusterTier(count)) {
            0 -> 36
            1 -> 44
            else -> 52
        }
        return circle("group-$size-$count", size, GROUP_COLOR, count.toString())
    }

    private fun itemIcon(item: ProviderStack): BitmapDescriptor {
        if (item.providers.size > 1) {
            return circle("stack-${item.selected}-${item.providers.size}", if (item.selected) 44 else 36, GROUP_COLOR, item.providers.size.toString())
        }
        val tipo = item.providers.first().tipo
        return circle("pin-${item.selected}-$tipo", if (item.selected) 36 else 26, providerTypeColor(tipo), null)
    }

    private fun circle(key: String, sizeDp: Int, color: Int, text: String?): BitmapDescriptor =
        icons.getOrPut(key) {
            val size = (sizeDp * density).toInt()
            val stroke = 2.5f * density
            val bitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(bitmap)
            val radius = size / 2f
            val paint = Paint(Paint.ANTI_ALIAS_FLAG)
            paint.color = WHITE
            canvas.drawCircle(radius, radius, radius, paint)
            paint.color = color
            canvas.drawCircle(radius, radius, radius - stroke, paint)
            if (text != null) {
                paint.color = WHITE
                paint.textAlign = Paint.Align.CENTER
                paint.typeface = Typeface.DEFAULT_BOLD
                paint.textSize = size * 0.4f
                canvas.drawText(text, radius, radius - (paint.descent() + paint.ascent()) / 2, paint)
            }
            BitmapDescriptorFactory.fromBitmap(bitmap)
        }

    private companion object {
        const val WHITE = 0xFFFFFFFF.toInt()
    }
}
