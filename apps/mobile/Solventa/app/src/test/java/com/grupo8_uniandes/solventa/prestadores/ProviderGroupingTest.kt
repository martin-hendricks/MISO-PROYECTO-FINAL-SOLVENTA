package com.grupo8_uniandes.solventa.prestadores

import androidx.test.core.app.ApplicationProvider
import android.content.Context
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderType
import com.grupo8_uniandes.solventa.ui.shell.clusterLabel
import com.grupo8_uniandes.solventa.ui.shell.clusterTier
import com.grupo8_uniandes.solventa.ui.shell.markerLabel
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class ProviderGroupingTest {
    @Test
    fun givenProvidersLessThan10mApart_whenStacking_thenTheyShareOneItem() {
        val first = chia("A", 4.86220, -74.05740)
        val fourMetersAway = chia("B", 4.86224, -74.05740)
        val twentyMetersAway = chia("C", 4.86238, -74.05740)

        val stacks = stackCoincident(listOf(first, fourMetersAway, twentyMetersAway), 10.0)

        assertEquals(listOf(listOf("A", "B"), listOf("C")), stacks.map { it.ids })
        assertEquals(4.8622, stacks.first().position.latitude, 0.0)
    }

    @Test
    fun givenTheThreeSabanaCentroProviders_whenGrouping_thenTheyGroupAt13AndSplitAt14() {
        val algorithm = ZoomCappedAlgorithm<ProviderStack>()
        algorithm.addItems(stackCoincident(SABANA_CENTRO))

        val at13 = algorithm.getClusters(13f)
        val at14 = algorithm.getClusters(14f)

        assertEquals(1, at13.size)
        assertEquals(3, at13.single().size)
        assertEquals(3, at14.size)
        assertEquals(setOf(1), at14.map { it.size }.toSet())
    }

    @Test
    fun givenACoincidentStack_whenZoomedIn_thenItStaysOneItem() {
        val algorithm = ZoomCappedAlgorithm<ProviderStack>()
        val pair = listOf(chia("A", 4.8622, -74.0574), chia("B", 4.8622, -74.0574))
        algorithm.addItems(stackCoincident(pair + SABANA_CENTRO.drop(1)))

        val at18 = algorithm.getClusters(18f)

        assertEquals(3, at18.size)
        assertEquals(listOf("A", "B"), at18.flatMap { it.items }.first { it.providers.size > 1 }.ids)
    }

    @Test
    fun givenCounts_whenSizingGroups_thenThreeTiersAreUsed() {
        assertEquals(0, clusterTier(9))
        assertEquals(1, clusterTier(10))
        assertEquals(1, clusterTier(49))
        assertEquals(2, clusterTier(50))
    }

    @Test
    fun givenAScreenReader_whenReadingMarkers_thenGroupsUseThePluralAndPinsTheirNameAndType() {
        val resources = ApplicationProvider.getApplicationContext<Context>().resources

        assertEquals("5 prestadores, toca para acercar", clusterLabel(resources, 5))
        assertEquals("1 prestador, toca para acercar", clusterLabel(resources, 1))
        val pin = ProviderStack(listOf(sample("PRE-BOG-06", 0.9)))
        assertEquals("Taller Moto Chapinero, Taller de motos", markerLabel(resources, pin))
        assertEquals("Taller Moto Chapinero", pin.title)
        assertEquals(null, pin.snippet)
        assertEquals(0f, pin.zIndex)
        assertEquals(1f, pin.copy(selected = true).zIndex)
    }
}

private val SABANA_CENTRO = listOf(
    chia("PRE-CHI-01", 4.8622, -74.0574),
    chia("PRE-CHI-04", 4.8605, -74.0558),
    chia("PRE-CHI-07", 4.8630, -74.0590),
)

private fun chia(id: String, lat: Double, lng: Double) = Provider(
    id = id,
    nombre = id,
    tipo = ProviderType.SERVICIO_TECNICO,
    ramos = listOf("proteccion-dispositivo"),
    direccion = "Cra 9 #10-15",
    ciudad = "Chía",
    barrio = "Centro",
    lat = lat,
    lng = lng,
    telefono = "601 555 3001",
    horario = "Lun–Vie 8:00–18:00",
    distanciaKm = null,
)
