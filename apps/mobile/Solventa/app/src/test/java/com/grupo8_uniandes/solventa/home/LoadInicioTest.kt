package com.grupo8_uniandes.solventa.home

import com.grupo8_uniandes.solventa.data.home.EmptyHomeRepository
import com.grupo8_uniandes.solventa.domain.home.ClaimCandidate
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

class LoadInicioTest {
    private val earlier = Instant.parse("2026-01-01T00:00:00Z")
    private val later = Instant.parse("2026-06-01T00:00:00Z")

    @Test
    fun givenConsultableQuote_whenLoaded_thenItIsTheOffer() {
        val panel = panel(
            HomeSituation(quotes = listOf(Quote("Q-1", consultable = true, becameCurrentAt = earlier))),
        )
        assertEquals("Q-1", panel.offerId)
    }

    @Test
    fun givenNewerQuoteThatCannotBeConsulted_whenLoaded_thenItIsDropped() {
        val panel = panel(
            HomeSituation(
                quotes = listOf(
                    Quote("Q-old", consultable = true, becameCurrentAt = earlier),
                    Quote("Q-new", consultable = false, becameCurrentAt = later),
                ),
            ),
        )
        assertEquals("Q-old", panel.offerId)
    }

    @Test
    fun givenTwoConsultableQuotes_whenLoaded_thenLatestTimestampWins() {
        val panel = panel(
            HomeSituation(
                quotes = listOf(
                    Quote("Q-old", consultable = true, becameCurrentAt = earlier),
                    Quote("Q-new", consultable = true, becameCurrentAt = later),
                ),
            ),
        )
        assertEquals("Q-new", panel.offerId)
        val olderLater = panel(
            HomeSituation(
                quotes = listOf(
                    Quote("Q-new", consultable = true, becameCurrentAt = later),
                    Quote("Q-old", consultable = true, becameCurrentAt = earlier),
                ),
            ),
        )
        assertEquals("Q-new", olderLater.offerId)
    }

    @Test
    fun givenEqualQuoteTimestamps_whenLoaded_thenLaterRowWins() {
        val panel = panel(
            HomeSituation(
                quotes = listOf(
                    Quote("Q-first", consultable = true, becameCurrentAt = earlier),
                    Quote("Q-second", consultable = true, becameCurrentAt = earlier),
                ),
            ),
        )
        assertEquals("Q-second", panel.offerId)
    }

    @Test
    fun givenNoConsultableQuote_whenLoaded_thenOfferIsAbsent() {
        val panel = panel(
            HomeSituation(quotes = listOf(Quote("Q-closed", consultable = false, becameCurrentAt = later))),
        )
        assertNull(panel.offerId)
    }

    @Test
    fun givenInactivePolicyWithLaterIssue_whenLoaded_thenItIsDropped() {
        val panel = panel(
            HomeSituation(
                policies = listOf(
                    PolicyCandidate("POL-old", active = true, issuedAt = earlier),
                    PolicyCandidate("POL-new", active = false, issuedAt = later),
                ),
            ),
        )
        assertEquals("POL-old", panel.policyId)
    }

    @Test
    fun givenTwoActivePolicies_whenLoaded_thenLatestIssueWinsAndTieKeepsLaterRow() {
        val latest = panel(
            HomeSituation(
                policies = listOf(
                    PolicyCandidate("POL-old", active = true, issuedAt = earlier),
                    PolicyCandidate("POL-new", active = true, issuedAt = later),
                ),
            ),
        )
        assertEquals("POL-new", latest.policyId)
        val tie = panel(
            HomeSituation(
                policies = listOf(
                    PolicyCandidate("POL-first", active = true, issuedAt = earlier),
                    PolicyCandidate("POL-second", active = true, issuedAt = earlier),
                ),
            ),
        )
        assertEquals("POL-second", tie.policyId)
    }

    @Test
    fun givenClosedClaim_whenLoaded_thenItIsDropped() {
        val panel = panel(
            HomeSituation(
                claims = listOf(
                    ClaimCandidate("CLM-open", inProgress = true, openedAt = earlier),
                    ClaimCandidate("CLM-closed", inProgress = false, openedAt = later),
                ),
            ),
        )
        assertEquals("CLM-open", panel.claimId)
    }

    @Test
    fun givenTwoClaimsInProgress_whenLoaded_thenLatestOpenWinsAndTieKeepsLaterRow() {
        val latest = panel(
            HomeSituation(
                claims = listOf(
                    ClaimCandidate("CLM-old", inProgress = true, openedAt = earlier),
                    ClaimCandidate("CLM-new", inProgress = true, openedAt = later),
                ),
            ),
        )
        assertEquals("CLM-new", latest.claimId)
        val tie = panel(
            HomeSituation(
                claims = listOf(
                    ClaimCandidate("CLM-first", inProgress = true, openedAt = earlier),
                    ClaimCandidate("CLM-second", inProgress = true, openedAt = earlier),
                ),
            ),
        )
        assertEquals("CLM-second", tie.claimId)
    }

    @Test
    fun givenOneSlotAtATime_whenLoaded_thenTheOthersStayEmpty() {
        val offer = panel(HomeSituation(quotes = listOf(Quote("Q-1", true, earlier))))
        assertEquals("Q-1", offer.offerId)
        assertNull(offer.policyId)
        assertNull(offer.claimId)
        assertFalse(offer.vidaCrediticia)

        val policy = panel(HomeSituation(policies = listOf(PolicyCandidate("POL-1", true, earlier))))
        assertNull(policy.offerId)
        assertEquals("POL-1", policy.policyId)
        assertNull(policy.claimId)

        val claim = panel(HomeSituation(claims = listOf(ClaimCandidate("CLM-1", true, earlier))))
        assertNull(claim.offerId)
        assertNull(claim.policyId)
        assertEquals("CLM-1", claim.claimId)
    }

    @Test
    fun givenEverySlot_whenLoaded_thenEachSelectedIdIsKept() {
        val panel = panel(
            HomeSituation(
                quotes = listOf(Quote("Q-1", true, earlier)),
                policies = listOf(PolicyCandidate("POL-1", true, earlier)),
                claims = listOf(ClaimCandidate("CLM-1", true, earlier)),
                origination = Origination(present = true),
            ),
        )
        assertEquals("Q-1", panel.offerId)
        assertEquals("POL-1", panel.policyId)
        assertEquals("CLM-1", panel.claimId)
        assertTrue(panel.vidaCrediticia)
    }

    @Test
    fun givenEmptyRepository_whenLoaded_thenNoSlots() {
        val panel = LoadInicio(EmptyHomeRepository()).panel()!!
        assertNull(panel.offerId)
        assertNull(panel.policyId)
        assertNull(panel.claimId)
        assertFalse(panel.vidaCrediticia)
    }

    @Test
    fun givenKeptQuote_whenAccepted_thenTheSameIdIsReportedAndNoPremiumExists() {
        val panel = panel(HomeSituation(quotes = listOf(Quote("Q-kept", true, later))))
        assertEquals("Q-kept", panel.offerId)
        assertTrue(panel.javaClass.declaredFields.none { it.name.contains("premium", ignoreCase = true) })
    }

    @Test
    fun givenOriginationOnly_whenLoaded_thenVidaDoesNotCreateOtherSlots() {
        val present = panel(HomeSituation(origination = Origination(present = true)))
        assertTrue(present.vidaCrediticia)
        assertNull(present.offerId)
        assertNull(present.policyId)
        assertNull(present.claimId)

        val absent = panel(HomeSituation(origination = Origination(present = false)))
        assertFalse(absent.vidaCrediticia)
    }

    private fun panel(situation: HomeSituation) =
        LoadInicio(HomeRepository { situation }).panel()!!
}
