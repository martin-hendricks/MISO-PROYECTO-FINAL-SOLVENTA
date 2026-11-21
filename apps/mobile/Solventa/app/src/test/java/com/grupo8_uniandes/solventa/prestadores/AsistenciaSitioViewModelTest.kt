package com.grupo8_uniandes.solventa.prestadores

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceResult
import com.grupo8_uniandes.solventa.domain.bff.assistance.ClaimProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderArea
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCity
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderPage
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderQuery
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.domain.bff.claim.PoliciesInForce
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssueRejection
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuedPolicy
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AsistenciaSitioViewModelTest {
    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenSeveralPolicies_whenTheCustomerEditsAndSubmits_thenTheChosenPolicyAndPlaceAreSent() {
        val assistance = RecordingAssistance()
        val viewModel = AsistenciaSitioViewModel(
            prestadorId = "PRE-1",
            assistance = assistance,
            locator = FixedLocator(GeoPoint(4.65, -74.08, 12)),
            policiesInForce = PoliciesInForce(Wallet(listOf(policy("POL-1", "SOAT"), policy("POL-2", "Vida")))),
        )

        assertTrue(viewModel.policiesLoaded.value)
        assertEquals(listOf("POL-1", "POL-2"), viewModel.policies.value.map { it.numero })
        assertEquals("", viewModel.form.value.policyValue)
        viewModel.onPolicy("PRE-NO")
        assertEquals("PRE-NO", viewModel.form.value.policyValue)
        viewModel.onPolicy("POL-2")
        viewModel.onDate("2026-03-12")
        viewModel.onDescription("Pantalla rota")
        viewModel.onPlace("Calle 72")
        assertEquals("POL-2 · Vida", viewModel.form.value.policyValue)
        assertEquals("Calle 72", viewModel.form.value.placeValue)

        viewModel.submit()

        assertEquals("PRE-1", assistance.last?.prestadorId)
        assertEquals(4.65, assistance.last!!.lat, 0.0)
        assertEquals(-74.08, assistance.last!!.lng, 0.0)
        assertEquals("POL-2", assistance.last!!.poliza)
    }

    @Test
    fun givenOnePolicyAndNoLocation_whenSubmitted_thenThatPolicyIsSentAtZero() {
        val assistance = RecordingAssistance()
        val viewModel = AsistenciaSitioViewModel(
            prestadorId = "PRE-9",
            assistance = assistance,
            locator = FixedLocator(null),
            policiesInForce = PoliciesInForce(Wallet(listOf(policy("POL-1", "SOAT")))),
        )

        assertEquals("POL-1 · SOAT", viewModel.form.value.policyValue)
        viewModel.submit()

        assertEquals(0.0, assistance.last!!.lat, 0.0)
        assertEquals(0.0, assistance.last!!.lng, 0.0)
        assertEquals("POL-1", assistance.last!!.poliza)
    }

    @Test
    fun givenTheLocatorFails_whenSubmitted_thenTheRequestStillGoesOut() {
        val assistance = RecordingAssistance()
        val viewModel = AsistenciaSitioViewModel(
            prestadorId = "PRE-3",
            assistance = assistance,
            locator = object : DeviceLocator {
                override suspend fun current(): GeoPoint? = error("sin gps")
            },
            policiesInForce = PoliciesInForce(Wallet(emptyList())),
        )

        viewModel.submit()

        assertEquals(0.0, assistance.last!!.lat, 0.0)
        assertEquals("", assistance.last!!.poliza)
    }

    private fun policy(numero: String, ramo: String) =
        PolicyEntry(numero, ramo, "ramo", "vigente", "2027-01-01")

    private class Wallet(private val rows: List<PolicyEntry>) : IssuanceRepository {
        override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = StandInAnswer.Failed
        override suspend fun rejected(): StandInAnswer<IssueRejection> = StandInAnswer.Failed
        override suspend fun policies(): StandInAnswer<List<PolicyEntry>> = StandInAnswer.Ready(rows)
        override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> = StandInAnswer.Failed
    }

    private class FixedLocator(private val point: GeoPoint?) : DeviceLocator {
        override suspend fun current(): GeoPoint? = point
    }

    private class RecordingAssistance : AssistanceRepository {
        var last: AssistanceRequest? = null

        override suspend fun providers(query: ProviderQuery): StandInAnswer<ProviderPage> = StandInAnswer.Failed
        override suspend fun cities(pais: String): StandInAnswer<List<ProviderCity>> = StandInAnswer.Failed
        override suspend fun providersNearClaim(id: String, area: ProviderArea?): StandInAnswer<ClaimProviders> =
            StandInAnswer.Failed

        override suspend fun request(body: AssistanceRequest): StandInAnswer<AssistanceResult> {
            last = body
            return StandInAnswer.Ready(AssistanceResult("ASI-1", "recibido"))
        }
    }
}
