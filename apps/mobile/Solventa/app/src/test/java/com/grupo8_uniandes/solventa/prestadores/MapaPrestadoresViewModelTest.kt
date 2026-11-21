package com.grupo8_uniandes.solventa.prestadores

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceResult
import com.grupo8_uniandes.solventa.domain.bff.assistance.ClaimProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.FindProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderArea
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCenter
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCity
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderPage
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderQuery
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.RegionChoice
import com.grupo8_uniandes.solventa.region.FakeRegionRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class MapaPrestadoresViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setMain() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenAFailedRead_whenLocationIsKnown_thenThePhaseIsError() = runTest(dispatcher) {
        val viewModel = viewModel(FakeAssistance(fail = true), locator = BOGOTA_FIX)

        viewModel.onLocationPermission(granted = true)
        advanceUntilIdle()

        assertEquals(ProviderMapPhase.Error, viewModel.state.value.phase)
        assertTrue(viewModel.state.value.providers.isEmpty())
    }

    @Test
    fun givenLocation_whenTheMapOpens_thenTheCameraStartsOnThePersonAtZoom14() = runTest(dispatcher) {
        val viewModel = viewModel(FakeAssistance(), locator = BOGOTA_FIX)

        viewModel.onLocationPermission(granted = true)
        advanceUntilIdle()

        val state = viewModel.state.value
        assertEquals(ProviderMapPhase.NearMe, state.phase)
        assertEquals(4.6432, state.cameraTarget!!.lat, 0.0)
        assertEquals(-74.0631, state.cameraTarget!!.lng, 0.0)
        assertEquals(14f, state.cameraTarget!!.zoom)
        assertTrue(state.canRecenter)
        assertNull(state.markedCity)
        assertEquals(listOf("Bogotá", "Medellín"), state.cities.map { it.nombre })
    }

    @Test
    fun givenThreeStopsWithin300ms_whenTheCameraIdles_thenOneAreaQueryCarriesTheLastAreaRamoAndOrigin() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        val viewModel = started(assistance, locator = BOGOTA_FIX)
        viewModel.selectRamo("soat-motocicleta")
        advanceUntilIdle()
        assistance.queries.clear()

        viewModel.onCameraIdle(AREA_A)
        advanceTimeBy(100)
        viewModel.onCameraIdle(AREA_B)
        advanceTimeBy(100)
        viewModel.onCameraIdle(CHAPINERO)
        advanceTimeBy(299)
        runCurrent()
        assertTrue(assistance.queries.isEmpty())
        advanceTimeBy(2)
        runCurrent()

        val query = assistance.queries.single()
        assertEquals(CHAPINERO, query.area)
        assertEquals("soat-motocicleta", query.ramo)
        assertEquals(4.6432, query.lat!!, 0.0)
        assertEquals(-74.0631, query.lng!!, 0.0)
        assertNull(query.radioKm)
        assertNull(query.ciudad)
    }

    @Test
    fun givenAnAreaInFlight_whenTheAnswerIsPending_thenThePreviousProvidersStay() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        val viewModel = started(assistance, locator = BOGOTA_FIX)
        val before = viewModel.state.value.providers
        assistance.latency = { if (it.area != null) 1_000 else 0 }
        assistance.rows = { if (it.area != null) listOf(sample("PRE-MED-01", 240.0)) else listOf(sample("PRE-BOG-06", 0.9)) }

        viewModel.onCameraIdle(MEDELLIN_AREA)
        advanceTimeBy(800)
        runCurrent()

        assertEquals(before, viewModel.state.value.providers)
        assertNotEquals(ProviderMapPhase.Loading, viewModel.state.value.phase)
        advanceUntilIdle()
        assertEquals("PRE-MED-01", viewModel.state.value.providers.single().id)
        assertEquals(240.0, viewModel.state.value.providers.single().distanciaKm!!, 0.0)
    }

    @Test
    fun givenAnOlderAreaAnsweringLate_whenANewerStopAnswers_thenTheOlderAnswerIsIgnored() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        val viewModel = started(assistance, locator = BOGOTA_FIX)
        assistance.latency = { if (it.area == AREA_A) 1_000 else 10 }
        assistance.rows = { if (it.area == AREA_A) listOf(sample("old", 1.0)) else listOf(sample("new", 2.0)) }

        viewModel.onCameraIdle(AREA_A)
        advanceTimeBy(350)
        viewModel.onCameraIdle(AREA_B)
        advanceUntilIdle()

        assertEquals("new", viewModel.state.value.providers.single().id)
        assertEquals(AREA_B, viewModel.state.value.area)
    }

    @Test
    fun givenATruncatedArea_whenItLoads_thenTheNoticeFlagIsSet() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        val viewModel = started(assistance, locator = BOGOTA_FIX)
        assistance.truncated = true

        viewModel.onCameraIdle(CHAPINERO)
        advanceUntilIdle()

        assertTrue(viewModel.state.value.truncado)
    }

    @Test
    fun givenAFailedAreaLoad_whenItFails_thenThePreviousProvidersStayWithTheErrorFlag() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        val viewModel = started(assistance, locator = BOGOTA_FIX)
        val before = viewModel.state.value.providers
        assistance.fail = true

        viewModel.onCameraIdle(CHAPINERO)
        advanceUntilIdle()

        assertEquals(before, viewModel.state.value.providers)
        assertTrue(viewModel.state.value.loadFailed)
        assertEquals(ProviderMapPhase.NearMe, viewModel.state.value.phase)

        assistance.fail = false
        assistance.queries.clear()
        viewModel.retry()
        advanceUntilIdle()
        assertFalse(viewModel.state.value.loadFailed)
        assertEquals(CHAPINERO, assistance.queries.single().area)
    }

    @Test
    fun givenThePersonPannedAway_whenRecentering_thenTheCameraTargetsThemAtZoom14() = runTest(dispatcher) {
        val viewModel = started(FakeAssistance(), locator = BOGOTA_FIX)
        val first = viewModel.state.value.cameraTarget!!
        viewModel.onUserPan()
        viewModel.onCameraIdle(MEDELLIN_AREA)
        advanceUntilIdle()

        viewModel.recenterOnMe()

        val target = viewModel.state.value.cameraTarget!!
        assertEquals(4.6432, target.lat, 0.0)
        assertEquals(14f, target.zoom)
        assertNotEquals(first.serial, target.serial)
    }

    @Test
    fun givenDeniedLocation_whenTheMapOpens_thenRecenterIsUnavailable() = runTest(dispatcher) {
        val viewModel = viewModel(FakeAssistance(), locator = null)

        viewModel.onLocationPermission(granted = false)
        advanceUntilIdle()
        val target = viewModel.state.value.cameraTarget
        viewModel.recenterOnMe()

        assertFalse(viewModel.state.value.canRecenter)
        assertEquals(target, viewModel.state.value.cameraTarget)
    }

    @Test
    fun givenAMarkerTap_whenSelecting_thenTheCardOpensSwapsAndClosesWithoutMovingTheCamera() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        assistance.rows = { listOf(sample("PRE-BOG-06", 0.9), sample("PRE-BOG-12", 1.4)) }
        val viewModel = started(assistance, locator = BOGOTA_FIX)
        val target = viewModel.state.value.cameraTarget

        viewModel.selectProvider("PRE-BOG-06")
        assertEquals(listOf("PRE-BOG-06"), viewModel.state.value.selectedIds)
        assertEquals("PRE-BOG-06", viewModel.state.value.selected.single().id)

        viewModel.selectProvider("PRE-BOG-12")
        assertEquals(listOf("PRE-BOG-12"), viewModel.state.value.selectedIds)

        viewModel.selectProviders(listOf("PRE-BOG-06", "PRE-BOG-12"))
        assertEquals(2, viewModel.state.value.selected.size)
        assertEquals(target, viewModel.state.value.cameraTarget)

        viewModel.closeCard()
        assertTrue(viewModel.state.value.selectedIds.isEmpty())
    }

    @Test
    fun givenAnOpenCard_whenAnAreaAnswerKeepsOrDropsTheProvider_thenTheCardStaysOrCloses() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        assistance.rows = { listOf(sample("PRE-BOG-12", 1.4)) }
        val viewModel = started(assistance, locator = BOGOTA_FIX)
        viewModel.selectProvider("PRE-BOG-12")

        viewModel.onCameraIdle(AREA_A)
        advanceUntilIdle()
        assertEquals(listOf("PRE-BOG-12"), viewModel.state.value.selectedIds)

        assistance.rows = { listOf(sample("PRE-BOG-06", 0.9)) }
        viewModel.selectRamo("soat-motocicleta")
        advanceUntilIdle()
        assertTrue(viewModel.state.value.selectedIds.isEmpty())
    }

    @Test
    fun givenPeruAndDeniedLocation_whenTheMapOpens_thenLimaIsMarkedAndTheSheetReadsItsName() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        val viewModel = viewModel(assistance, locator = null, region = Region.Peru)

        viewModel.onLocationPermission(granted = false)
        advanceUntilIdle()

        val state = viewModel.state.value
        assertEquals("PE", assistance.paises.single())
        assertEquals(listOf("Lima", "Arequipa", "Trujillo"), state.cities.map { it.nombre })
        assertEquals("Lima", state.markedCity)
        assertEquals("Lima", state.ciudad)
        assertEquals(ProviderPlacement.City, state.placement)
        assertEquals(ProviderMapPhase.ChooseCity, state.phase)
        assertFalse(state.canRecenter)
        assertEquals(CameraTarget(-12.0464, -77.0428, 11f, state.cameraTarget!!.serial), state.cameraTarget)
        val query = assistance.queries.single()
        assertEquals("Lima", query.ciudad)
        assertEquals("PE", query.pais)
        assertNull(query.lat)
    }

    @Test
    fun givenTheChips_whenACityIsChosenAndThePersonDrags_thenItIsMarkedThenUnmarked() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        val viewModel = viewModel(assistance, locator = null, region = Region.Peru)
        viewModel.onLocationPermission(granted = false)
        advanceUntilIdle()
        viewModel.selectRamo("vida-crediticia")
        advanceUntilIdle()
        viewModel.onCameraIdle(AREA_A)
        advanceUntilIdle()
        assistance.queries.clear()

        viewModel.selectCity(TRUJILLO)
        advanceUntilIdle()

        val state = viewModel.state.value
        assertEquals("Trujillo", state.markedCity)
        assertEquals(13f, state.cameraTarget!!.zoom)
        assertEquals(-8.1116, state.cameraTarget!!.lat, 0.0)
        assertEquals("vida-crediticia", state.ramo)
        assertTrue(assistance.queries.isEmpty())

        viewModel.onUserPan()
        assertNull(viewModel.state.value.markedCity)
    }

    @Test
    fun givenACountryWithoutProviders_whenTheMapOpens_thenTheCountryEmptyPhaseShows() = runTest(dispatcher) {
        val assistance = FakeAssistance(cities = emptyMap())
        val viewModel = viewModel(assistance, locator = null, region = Region.Mexico)

        viewModel.onLocationPermission(granted = false)
        advanceUntilIdle()

        assertEquals(ProviderMapPhase.CountryEmpty, viewModel.state.value.phase)
        assertEquals("MX", viewModel.state.value.pais)
        assertTrue(viewModel.state.value.cities.isEmpty())
        assertTrue(assistance.queries.isEmpty())
    }

    @Test
    fun givenLocation_whenJumpingToACity_thenDistancesStayMeasuredFromThePerson() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        val viewModel = started(assistance, locator = BOGOTA_FIX)
        viewModel.onCameraIdle(CHAPINERO)
        advanceUntilIdle()
        assistance.queries.clear()

        viewModel.selectCity(MEDELLIN)
        viewModel.onCameraIdle(MEDELLIN_AREA)
        advanceUntilIdle()

        val query = assistance.queries.single()
        assertEquals(MEDELLIN_AREA, query.area)
        assertEquals(4.6432, query.lat!!, 0.0)
        assertEquals(ProviderPlacement.Near, viewModel.state.value.placement)
        assertEquals("Medellín", viewModel.state.value.markedCity)
    }

    @Test
    fun givenAClaim_whenTheMapOpensAndMoves_thenItStartsAtTheGeotagAndAreasGoToTheClaimRoute() = runTest(dispatcher) {
        val assistance = FakeAssistance()
        val viewModel = viewModel(assistance, locator = BOGOTA_FIX, claimId = "SIN-1")

        viewModel.onLocationPermission(granted = true)
        advanceUntilIdle()
        val opened = viewModel.state.value
        assertEquals(ProviderMapPhase.ClaimMode, opened.phase)
        assertEquals(CameraTarget(4.626, -74.15, 14f, opened.cameraTarget!!.serial), opened.cameraTarget)
        assertTrue(opened.cities.isEmpty())
        assertTrue(assistance.paises.isEmpty())
        assertEquals("soat-motocicleta", opened.ramoFijo)
        assertTrue(opened.distanceFromEvent)

        viewModel.onCameraIdle(CHAPINERO)
        advanceUntilIdle()

        assertEquals(listOf(null, CHAPINERO), assistance.claimAreas)
        assertTrue(assistance.queries.isEmpty())
        val state = viewModel.state.value
        assertEquals("PRE-BOG-21", state.providers.single().id)
        val grouped = stackCoincident(state.providers).flatMap { it.ids }
        assertEquals(state.providers.map { it.id }, grouped)
        assertTrue(state.distanceFromEvent)
    }

    private fun TestScope.started(assistance: FakeAssistance, locator: GeoPoint?): MapaPrestadoresViewModel {
        val viewModel = viewModel(assistance, locator)
        viewModel.onLocationPermission(granted = true)
        advanceUntilIdle()
        return viewModel
    }
}

private val BOGOTA_FIX = GeoPoint(4.6432, -74.0631, 8)
private val AREA_A = ProviderArea(norte = 4.70, sur = 4.60, este = -74.00, oeste = -74.10)
private val AREA_B = ProviderArea(norte = 4.71, sur = 4.61, este = -74.01, oeste = -74.11)
private val CHAPINERO = ProviderArea(norte = 4.66, sur = 4.62, este = -74.05, oeste = -74.08)
private val MEDELLIN_AREA = ProviderArea(norte = 6.30, sur = 6.19, este = -75.52, oeste = -75.64)
private val BOGOTA = ProviderCity("Bogotá", 4.6097, -74.0817, 12, 30)
private val MEDELLIN = ProviderCity("Medellín", 6.2442, -75.5812, 13, 20)
private val TRUJILLO = ProviderCity("Trujillo", -8.1116, -79.0288, 13, 4)
private val CITIES = mapOf(
    "CO" to listOf(BOGOTA, MEDELLIN),
    "PE" to listOf(
        ProviderCity("Lima", -12.0464, -77.0428, 11, 5),
        ProviderCity("Arequipa", -16.409, -71.5375, 13, 4),
        TRUJILLO,
    ),
)

private class FakeAssistance(
    var fail: Boolean = false,
    private val cities: Map<String, List<ProviderCity>> = CITIES,
) : AssistanceRepository {
    val queries = mutableListOf<ProviderQuery>()
    val claimAreas = mutableListOf<ProviderArea?>()
    val paises = mutableListOf<String>()
    var truncated = false
    var latency: (ProviderQuery) -> Long = { 0 }
    var rows: (ProviderQuery) -> List<com.grupo8_uniandes.solventa.domain.bff.assistance.Provider> =
        { listOf(sample("PRE-BOG-06", 0.9)) }

    override suspend fun providers(query: ProviderQuery): StandInAnswer<ProviderPage> {
        queries += query
        delay(latency(query))
        if (fail) return StandInAnswer.Failed
        return StandInAnswer.Ready(
            ProviderPage(
                centro = query.lat?.let { ProviderCenter(it, query.lng!!, "posicion") },
                radioKm = query.radioKm,
                prestadores = rows(query),
                truncado = truncated,
            ),
        )
    }

    override suspend fun cities(pais: String): StandInAnswer<List<ProviderCity>> {
        paises += pais
        if (fail) return StandInAnswer.Failed
        return StandInAnswer.Ready(cities[pais].orEmpty())
    }

    override suspend fun providersNearClaim(id: String, area: ProviderArea?): StandInAnswer<ClaimProviders> {
        claimAreas += area
        if (fail) return StandInAnswer.Failed
        return StandInAnswer.Ready(
            ClaimProviders(
                siniestroId = id,
                numero = "SIN-1988",
                ramo = "soat-motocicleta",
                ramoFijo = "soat-motocicleta",
                sinGeoetiqueta = false,
                centro = ProviderCenter(4.626, -74.15, "siniestro"),
                radioKm = if (area == null) 10.0 else null,
                prestadores = listOf(sample(if (area == null) "PRE-BOG-06" else "PRE-BOG-21", 0.8)),
            ),
        )
    }

    override suspend fun request(body: AssistanceRequest): StandInAnswer<AssistanceResult> = StandInAnswer.Failed
}

private fun viewModel(
    assistance: FakeAssistance,
    locator: GeoPoint?,
    region: Region = Region.Colombia,
    claimId: String? = null,
) = MapaPrestadoresViewModel(
    FindProviders(assistance),
    object : DeviceLocator {
        override suspend fun current(): GeoPoint? = locator
    },
    FakeRegionRepository(RegionChoice(appliedRegion = region, draftRegion = region, firstLaunchCompleted = true)),
    mapsKey = "",
    claimId = claimId,
)
