package com.grupo8_uniandes.solventa.home

import com.grupo8_uniandes.solventa.domain.home.ClaimCandidate
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.domain.home.HomeRepository
import com.grupo8_uniandes.solventa.domain.home.HomeSituation
import com.grupo8_uniandes.solventa.domain.home.LoadInicio
import com.grupo8_uniandes.solventa.domain.home.Origination
import com.grupo8_uniandes.solventa.domain.home.PolicyCandidate
import com.grupo8_uniandes.solventa.domain.home.Quote
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.Instant

class HomeViewModelTest {
    @Test
    fun givenEmptyRepository_whenHomeLoads_thenNoSlots() {
        val panel = HomeViewModel().state.value.panel
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
}
