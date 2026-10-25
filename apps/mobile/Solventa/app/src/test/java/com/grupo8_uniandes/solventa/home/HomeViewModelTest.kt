package com.grupo8_uniandes.solventa.home

import com.grupo8_uniandes.solventa.data.home.EmptyHomeRepository
import com.grupo8_uniandes.solventa.data.home.StandInHomeRepository
import com.grupo8_uniandes.solventa.domain.home.ClaimCandidate
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.domain.home.HomeRepository
import com.grupo8_uniandes.solventa.domain.home.HomeSituation
import com.grupo8_uniandes.solventa.domain.home.LoadInicio
import com.grupo8_uniandes.solventa.domain.home.Origination
import com.grupo8_uniandes.solventa.domain.home.PolicyCandidate
import com.grupo8_uniandes.solventa.domain.home.Quote
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.Instant

class HomeViewModelTest {
    @Test
    fun givenStandInHome_whenDefaultLoads_thenPublishedOfferIsCurrent() {
        val panel = HomeViewModel(LoadInicio(StandInHomeRepository())).state.value.panel
        assertEquals("COT-1042", panel.offerId)
        assertEquals("POL-88219-CO", panel.policyId)
        assertEquals("SIN-441", panel.claimId)
        assertFalse(panel.vidaCrediticia)
    }

    @Test
    fun givenEmptyRepository_whenHomeLoads_thenNoSlots() {
        val panel = HomeViewModel(LoadInicio(EmptyHomeRepository())).state.value.panel
        assertNull(panel.offerId)
        assertNull(panel.policyId)
        assertNull(panel.claimId)
        assertFalse(panel.vidaCrediticia)
    }

    @Test
    fun givenSituation_whenHomeLoads_thenOnlySelectedSlots() {
        val at = Instant.parse("2026-03-01T00:00:00Z")
        val viewModel = HomeViewModel(
            LoadInicio(
                HomeRepository {
                    HomeSituation(
                        quotes = listOf(
                            Quote("Q-drop", consultable = false, becameCurrentAt = at),
                            Quote("Q-kept", consultable = true, becameCurrentAt = at),
                        ),
                        policies = listOf(PolicyCandidate("POL-1", active = true, issuedAt = at)),
                        claims = listOf(ClaimCandidate("CLM-1", inProgress = true, openedAt = at)),
                        origination = Origination(present = false),
                    )
                },
            ),
        )
        val panel = viewModel.state.value.panel
        assertEquals("Q-kept", panel.offerId)
        assertEquals("POL-1", panel.policyId)
        assertEquals("CLM-1", panel.claimId)
        assertFalse(panel.vidaCrediticia)
    }

    @Test
    fun givenKeptOffer_whenRead_thenAcceptIdMatchesAndThereIsNoPremium() {
        val at = Instant.parse("2026-03-01T00:00:00Z")
        val panel = HomeViewModel(
            LoadInicio(
                HomeRepository {
                    HomeSituation(quotes = listOf(Quote("Q-kept", consultable = true, becameCurrentAt = at)))
                },
            ),
        ).state.value.panel
        assertEquals("Q-kept", panel.offerId)
        assertTrue(HomePanel::class.java.declaredFields.none { it.name.contains("premium", ignoreCase = true) })
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenANewSituation_whenRefresh_thenThePanelFollowsIt() {
        val dispatcher = UnconfinedTestDispatcher()
        Dispatchers.setMain(dispatcher)
        try {
            var situation = HomeSituation()
            val viewModel = HomeViewModel(
                LoadInicio(HomeRepository { situation }),
                reloadDispatcher = dispatcher,
            )
            assertNull(viewModel.state.value.panel.offerId)
            val at = Instant.parse("2026-03-01T00:00:00Z")
            situation = HomeSituation(
                quotes = listOf(Quote("Q-new", consultable = true, becameCurrentAt = at)),
            )

            viewModel.refresh()

            assertEquals("Q-new", viewModel.state.value.panel.offerId)
            assertNull(viewModel.state.value.panel.policyId)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenAShownPanel_whenRefreshFails_thenThePanelStaysAndFailedIsSet() {
        val dispatcher = UnconfinedTestDispatcher()
        Dispatchers.setMain(dispatcher)
        try {
            var available = true
            val at = Instant.parse("2026-03-01T00:00:00Z")
            val viewModel = HomeViewModel(
                LoadInicio(
                    HomeRepository {
                        if (available) {
                            HomeSituation(quotes = listOf(Quote("Q-kept", consultable = true, becameCurrentAt = at)))
                        } else {
                            null
                        }
                    },
                ),
                reloadDispatcher = dispatcher,
            )
            assertEquals("Q-kept", viewModel.state.value.panel.offerId)
            assertFalse(viewModel.state.value.failed)
            available = false

            viewModel.refresh()

            assertEquals("Q-kept", viewModel.state.value.panel.offerId)
            assertTrue(viewModel.state.value.failed)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenALoadInFlight_whenRefreshAgain_thenOnlyTheFirstCallRuns() {
        val dispatcher = StandardTestDispatcher()
        Dispatchers.setMain(dispatcher)
        try {
            var calls = 0
            val viewModel = HomeViewModel(
                LoadInicio(
                    HomeRepository {
                        calls += 1
                        HomeSituation()
                    },
                ),
                reloadDispatcher = dispatcher,
            )
            assertEquals(1, calls)

            viewModel.refresh()
            viewModel.refresh()
            dispatcher.scheduler.advanceUntilIdle()

            assertEquals(2, calls)
            assertFalse(viewModel.state.value.failed)
        } finally {
            Dispatchers.resetMain()
        }
    }
}
