package com.grupo8_uniandes.solventa.prestadores

import com.google.android.gms.maps.model.LatLng
import com.google.maps.android.clustering.Cluster
import com.google.maps.android.clustering.ClusterItem
import com.google.maps.android.clustering.algo.Algorithm
import com.google.maps.android.clustering.algo.NonHierarchicalDistanceBasedAlgorithm
import com.google.maps.android.clustering.algo.StaticCluster
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

const val STACK_METERS = 10.0
const val GROUP_DISTANCE_DP = 60
const val SPLIT_ZOOM = 14f

data class ProviderStack(
    val providers: List<Provider>,
    val selected: Boolean = false,
) : ClusterItem {
    val ids: List<String> get() = providers.map { it.id }

    override fun getPosition(): LatLng = LatLng(providers.first().lat, providers.first().lng)

    override fun getTitle(): String = providers.first().nombre

    override fun getSnippet(): String? = null

    override fun getZIndex(): Float = if (selected) 1f else 0f
}

fun stackCoincident(providers: List<Provider>, meters: Double = STACK_METERS): List<ProviderStack> {
    val stacks = mutableListOf<MutableList<Provider>>()
    providers.forEach { provider ->
        val stack = stacks.firstOrNull { metersBetween(it.first(), provider) < meters }
        if (stack != null) stack += provider else stacks += mutableListOf(provider)
    }
    return stacks.map { ProviderStack(it) }
}

class ZoomCappedAlgorithm<T : ClusterItem>(
    private val inner: Algorithm<T> = NonHierarchicalDistanceBasedAlgorithm<T>().apply {
        maxDistanceBetweenClusteredItems = GROUP_DISTANCE_DP
    },
    private val splitZoom: Float = SPLIT_ZOOM,
) : Algorithm<T> by inner {
    override fun getClusters(zoom: Float): Set<out Cluster<T>> {
        if (zoom < splitZoom) return inner.getClusters(zoom)
        return inner.items.mapTo(linkedSetOf()) { item ->
            StaticCluster<T>(item.position).apply { add(item) }
        }
    }
}

private fun metersBetween(a: Provider, b: Provider): Double {
    val dLat = Math.toRadians(b.lat - a.lat)
    val dLng = Math.toRadians(b.lng - a.lng)
    val h = sin(dLat / 2).pow(2) +
        cos(Math.toRadians(a.lat)) * cos(Math.toRadians(b.lat)) * sin(dLng / 2).pow(2)
    return 2 * EARTH_METERS * asin(sqrt(h))
}

private const val EARTH_METERS = 6_371_000.0
