package com.grupo8_uniandes.solventa.prestadores

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceResult
import com.grupo8_uniandes.solventa.domain.bff.assistance.ClaimProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.FindProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderPage
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderQuery
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
class MapaPrestadoresViewModelTest {
    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenDeniedPermission_whenTheMapOpens_thenTheCityPickerIsOffered() {
        val viewModel = MapaPrestadoresViewModel(FindProviders(FailedAssistance()), locator = null, mapsKey = "")

        viewModel.onLocationPermission(granted = false)

        assertEquals(ProviderMapPhase.ChooseCity, viewModel.state.value.phase)
        assertEquals(ProviderPlacement.City, viewModel.state.value.placement)
        assertTrue(viewModel.state.value.providers.isEmpty())
    }

    @Test
    fun givenAGrantedFixThatCannotBeRead_whenTheMapOpens_thenItAsksForACity() {
        val viewModel = MapaPrestadoresViewModel(FindProviders(FailedAssistance()), locator = null, mapsKey = "")

        viewModel.onLocationPermission(granted = true)

        assertEquals(ProviderMapPhase.ChooseCity, viewModel.state.value.phase)
        assertNotEquals(ProviderMapPhase.Empty, viewModel.state.value.phase)
    }

    @Test
    fun givenAFailedRead_whenLocationIsKnown_thenThePhaseIsError() {
        val viewModel = MapaPrestadoresViewModel(
            FindProviders(FailedAssistance()),
            locator = GeoPoint(4.64, -74.06, 8),
            mapsKey = "",
        )

        viewModel.onLocationPermission(granted = true)

        assertEquals(ProviderMapPhase.Error, viewModel.state.value.phase)
        assertNotEquals(ProviderMapPhase.Empty, viewModel.state.value.phase)
        assertTrue(viewModel.state.value.providers.isEmpty())
    }
}

private class FailedAssistance : AssistanceRepository {
    override suspend fun providers(query: ProviderQuery): StandInAnswer<ProviderPage> = StandInAnswer.Failed

    override suspend fun providersNearClaim(id: String): StandInAnswer<ClaimProviders> = StandInAnswer.Failed

    override suspend fun request(body: AssistanceRequest): StandInAnswer<AssistanceResult> = StandInAnswer.Failed
}

private fun MapaPrestadoresViewModel(
    find: FindProviders,
    locator: GeoPoint?,
    mapsKey: String,
) = MapaPrestadoresViewModel(
    find,
    object : DeviceLocator {
        override suspend fun current(): GeoPoint? = locator
    },
    mapsKey,
)
