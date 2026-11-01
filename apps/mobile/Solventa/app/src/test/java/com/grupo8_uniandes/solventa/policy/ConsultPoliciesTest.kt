package com.grupo8_uniandes.solventa.policy

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.issuance.ConsultPolicies
import com.grupo8_uniandes.solventa.domain.bff.issuance.DEVICE_GUIDANCE
import com.grupo8_uniandes.solventa.domain.bff.issuance.InMemoryPolicyStore
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssueRejection
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuedPolicy
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.domain.bff.issuance.detailMeta
import com.grupo8_uniandes.solventa.domain.bff.issuance.guidanceFor
import com.grupo8_uniandes.solventa.domain.bff.issuance.listBody
import com.grupo8_uniandes.solventa.domain.bff.issuance.listMeta
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ConsultPoliciesTest {
    @Test
    fun givenTheReviewWallet_whenListed_thenTheCardsMatchTheReviewSet() = runBlocking {
        val consult = ConsultPolicies(scripted(wallet = StandInAnswer.Ready(reviewWallet())), InMemoryPolicyStore())
        val result = consult.list()
        assertEquals(listOf("POL-88219-CO", "POL-11002-CO"), result.policies.map { it.numero })
        assertEquals("Protección de dispositivo · Robo, Pantalla, Hurto", listBody(result.policies[0]))
        assertEquals("Vigente · vence 12 mar 2027", listMeta(result.policies[0]))
        assertEquals("Microseguro de vida · amparo de vida", listBody(result.policies[1]))
        assertEquals("Por vencer · en 7 días", listMeta(result.policies[1]))
        assertFalse(result.notice)
    }

    @Test
    fun givenNoPolicies_whenListed_thenTheResultIsEmpty() = runBlocking {
        val consult = ConsultPolicies(scripted(wallet = StandInAnswer.Ready(emptyList())), InMemoryPolicyStore())
        val result = consult.list()
        assertTrue(result.policies.isEmpty())
        assertTrue(result.empty)
    }

    @Test
    fun givenTheDevicePolicy_whenOpened_thenTheCoveragesAndGuidanceArePresent() = runBlocking {
        val consult = ConsultPolicies(scripted(detail = deviceDetail()), InMemoryPolicyStore())
        val opened = consult.open("POL-88219-CO")
        val detail = opened.detail!!
        assertEquals("Robo y Pantalla", detail.resumen)
        assertEquals(DEVICE_GUIDANCE, guidanceFor(detail))
        assertEquals("Vigente hasta 12 mar 2027 · sigue renovación", detailMeta(detail))
    }

    @Test
    fun givenTheLifePolicy_whenOpened_thenTheDeviceGuidanceIsAbsent() = runBlocking {
        val consult = ConsultPolicies(
            scripted(wallet = StandInAnswer.Ready(reviewWallet()), detail = deviceDetail()),
            InMemoryPolicyStore(),
        )
        consult.list()
        val opened = consult.open("POL-11002-CO").detail!!
        assertEquals("amparo de vida", opened.resumen)
        assertEquals("", guidanceFor(opened))
        assertEquals("Por vencer · en 7 días", detailMeta(opened))
        val other = WalletEntry("POL-1", "otro ramo", "resto", "otro", "2027-03-12")
        assertEquals("otro", listMeta(other))
        assertEquals(
            "Vigente · vence 12 mar 2027",
            detailMeta(PolicyDetail("POL-1", "otro ramo", "resto", "vigente", "2027-03-12", "")),
        )
        assertEquals("otro", detailMeta(PolicyDetail("POL-1", "otro ramo", "resto", "otro", "2027-03-12", "")))
        assertEquals(
            "Por vencer · en 7 días",
            detailMeta(PolicyDetail("POL-88219-CO", "Protección de dispositivo", "Robo y Pantalla", "por_vencer", "2027-03-12", "")),
        )
    }

    @Test
    fun givenALifeDetailForThatNumber_whenOpened_thenTheDeviceParagraphIsDropped() = runBlocking {
        val life = StandInAnswer.Ready(
            PolicyDetail("POL-11002-CO", "Microseguro de vida", "amparo de vida", "por_vencer", "2026-11-06", DEVICE_GUIDANCE),
        )
        val opened = ConsultPolicies(scripted(detail = life), InMemoryPolicyStore()).open("POL-11002-CO").detail!!
        assertEquals("", opened.queHacer)
        assertEquals("amparo de vida", opened.resumen)
    }

    @Test
    fun givenADetailForAnotherNumberAndNoSavedWallet_whenOpened_thenGuidanceIsCleared() = runBlocking {
        val consult = ConsultPolicies(scripted(detail = deviceDetail()), InMemoryPolicyStore())
        val opened = consult.open("POL-11002-CO").detail!!
        assertEquals("POL-11002-CO", opened.numero)
        assertEquals("", opened.queHacer)
    }

    @Test
    fun givenASavedDetail_whenAFailureIsFollowedBySuccess_thenTheNoticeIsSet() = runBlocking {
        var detail: StandInAnswer<PolicyDetail> = deviceDetail()
        val consult = ConsultPolicies(
            object : IssuanceRepository {
                override suspend fun accept(cotizacionId: String) = StandInAnswer.Failed as StandInAnswer<IssuedPolicy>
                override suspend fun rejected() = StandInAnswer.Failed as StandInAnswer<IssueRejection>
                override suspend fun wallet() = StandInAnswer.Failed as StandInAnswer<List<WalletEntry>>
                override suspend fun detail(numero: String) = detail
            },
            InMemoryPolicyStore(),
        )
        assertFalse(consult.open("POL-88219-CO").notice)
        detail = StandInAnswer.Failed
        assertFalse(consult.open("POL-88219-CO").notice)
        detail = deviceDetail()
        assertTrue(consult.open("POL-88219-CO").notice)
    }

    @Test
    fun givenASavedConsultation_whenTheNextReadFails_thenTheSavedCoverageRemains() = runBlocking {
        var wallet: StandInAnswer<List<WalletEntry>> = StandInAnswer.Ready(reviewWallet())
        var detail: StandInAnswer<PolicyDetail> = deviceDetail()
        val consult = ConsultPolicies(
            object : IssuanceRepository {
                override suspend fun accept(cotizacionId: String) = StandInAnswer.Failed as StandInAnswer<IssuedPolicy>
                override suspend fun rejected() = StandInAnswer.Failed as StandInAnswer<IssueRejection>
                override suspend fun wallet() = wallet
                override suspend fun detail(numero: String) = detail
            },
            InMemoryPolicyStore(),
        )
        consult.list()
        consult.open("POL-88219-CO")
        wallet = StandInAnswer.Failed
        detail = StandInAnswer.Failed
        val listed = consult.list()
        val opened = consult.open("POL-88219-CO")
        assertEquals(listOf("POL-88219-CO", "POL-11002-CO"), listed.policies.map { it.numero })
        assertEquals("Robo y Pantalla", opened.detail?.resumen)
        assertFalse(listed.notice)
        assertFalse(opened.notice)
    }

    @Test
    fun givenNothingSaved_whenTheReadFails_thenTheConsultationIsEmpty() = runBlocking {
        val consult = ConsultPolicies(scripted(), InMemoryPolicyStore())
        val listed = consult.list()
        val opened = consult.open("POL-88219-CO")
        assertTrue(listed.policies.isEmpty())
        assertTrue(listed.empty)
        assertTrue(opened.missing)
        assertEquals(null, opened.detail)
    }

    @Test
    fun givenAFailureThenAReadyRead_whenListed_thenTheNoticeFollowsOnlyThatRecovery() = runBlocking {
        var wallet: StandInAnswer<List<WalletEntry>> = StandInAnswer.Failed
        val consult = ConsultPolicies(
            object : IssuanceRepository {
                override suspend fun accept(cotizacionId: String) = StandInAnswer.Failed as StandInAnswer<IssuedPolicy>
                override suspend fun rejected() = StandInAnswer.Failed as StandInAnswer<IssueRejection>
                override suspend fun wallet() = wallet
                override suspend fun detail(numero: String) = StandInAnswer.Failed
            },
            InMemoryPolicyStore(),
        )
        assertFalse(consult.list().notice)
        wallet = StandInAnswer.Ready(reviewWallet())
        assertFalse(consult.list().notice)
        wallet = StandInAnswer.Failed
        consult.list()
        wallet = StandInAnswer.Ready(reviewWallet())
        assertTrue(consult.list().notice)
        assertFalse(consult.list().notice)
    }
}

private fun reviewWallet() = listOf(
    WalletEntry("POL-88219-CO", "Protección de dispositivo", "Robo, Pantalla, Hurto", "vigente", "2027-03-12"),
    WalletEntry("POL-11002-CO", "Microseguro de vida", "amparo de vida", "por_vencer", "2026-11-06"),
)

private fun deviceDetail() = StandInAnswer.Ready(
    PolicyDetail(
        "POL-88219-CO",
        "Protección de dispositivo",
        "Robo y Pantalla",
        "vigente",
        "2027-03-12",
        DEVICE_GUIDANCE,
    ),
)

private fun scripted(
    wallet: StandInAnswer<List<WalletEntry>> = StandInAnswer.Failed,
    detail: StandInAnswer<PolicyDetail> = StandInAnswer.Failed,
) = object : IssuanceRepository {
    override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = StandInAnswer.Failed

    override suspend fun rejected(): StandInAnswer<IssueRejection> = StandInAnswer.Failed

    override suspend fun wallet(): StandInAnswer<List<WalletEntry>> = wallet

    override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> = detail
}
