package com.grupo8_uniandes.solventa.home

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Test

class HomeViewModelTest {
    @Test
    fun givenNoOfferAndNoPolicy_whenHomeLoads_thenQuoteOnly() {
        val state = HomeViewModel().state.value
        assertEquals("Nueva cotización", state.quoteActionLabel)
        assertNull(state.summary.offer)
        assertNull(state.summary.policy)
        assertFalse(state.showEnrichedHome)
    }

    @Test
    fun givenOfferOnly_whenHomeLoads_thenOfferCardAndQuote() {
        val state = HomeViewModel(HomeSummary(offer = OfferSummary("SOAT motocicleta"))).state.value
        assertEquals("Nueva cotización", state.quoteActionLabel)
        assertEquals("SOAT motocicleta", state.summary.offer?.label)
        assertNull(state.summary.policy)
        assertFalse(state.showEnrichedHome)
    }

    @Test
    fun givenPolicyOnly_whenHomeLoads_thenPolicyCardAndQuote() {
        val state = HomeViewModel(HomeSummary(policy = PolicySummary("SOL-0001"))).state.value
        assertEquals("Nueva cotización", state.quoteActionLabel)
        assertNull(state.summary.offer)
        assertEquals("SOL-0001", state.summary.policy?.policyId)
        assertFalse(state.showEnrichedHome)
    }

    @Test
    fun givenOfferAndPolicy_whenHomeLoads_thenBothCardsAndQuote() {
        val state = HomeViewModel(
            HomeSummary(
                offer = OfferSummary("SOAT motocicleta"),
                policy = PolicySummary("SOL-0001"),
            ),
        ).state.value
        assertEquals("SOAT motocicleta", state.summary.offer?.label)
        assertEquals("SOL-0001", state.summary.policy?.policyId)
        assertEquals("Nueva cotización", state.quoteActionLabel)
        assertFalse(state.showEnrichedHome)
    }

    @Test
    fun perfilExposesOnlyIdiomaYRegion() {
        val entries = HomeViewModel().profileEntries
        assertEquals(1, entries.size)
        assertEquals("IdiomaRegion", entries.single().id)
        assertEquals("Idioma y región", entries.single().label)
    }
}
