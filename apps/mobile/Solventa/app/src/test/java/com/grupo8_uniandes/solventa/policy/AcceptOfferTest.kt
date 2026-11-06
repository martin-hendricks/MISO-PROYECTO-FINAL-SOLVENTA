package com.grupo8_uniandes.solventa.policy

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.issuance.AcceptOffer
import com.grupo8_uniandes.solventa.domain.bff.issuance.AcceptOutcome
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssueRejection
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuedPolicy
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.yield
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

private const val REASON = "La suscripción automática rechazó el riesgo del dispositivo cotizado."

class AcceptOfferTest {
    @Test
    fun givenAnAcceptInProgress_whenAcceptIsCalledAgain_thenTheRepositoryIsNotCalledAgain() = runBlocking {
        val gate = CompletableDeferred<Unit>()
        var calls = 0
        val useCase = AcceptOffer(scripted(onAccept = {
            calls += 1
            gate.await()
            issued()
        }))
        val first = async { useCase.accept("COT-1042") }
        while (calls == 0) yield()
        val second = useCase.accept("COT-1042")
        assertEquals(AcceptOutcome.Ignored, second)
        assertEquals(1, calls)
        gate.complete(Unit)
        val outcome = first.await()
        assertTrue(outcome is AcceptOutcome.Issued)
    }

    @Test
    fun givenASuccessfulAccept_whenTheResultIsRead_thenTheReviewPolicyIsReturned() = runBlocking {
        val useCase = AcceptOffer(scripted(onAccept = { issued() }))
        val outcome = useCase.accept("COT-1042") as AcceptOutcome.Issued
        assertEquals("POL-88219-CO", outcome.policy.numero)
        assertEquals("Protección de dispositivo", outcome.policy.ramo)
    }

    @Test
    fun givenARefusal_whenTheResultIsRead_thenTheReasonHasNoPolicyNumber() = runBlocking {
        val useCase = AcceptOffer(
            scripted(
                onAccept = { StandInAnswer.Failed },
                onRejected = { StandInAnswer.Ready(IssueRejection("rechazada", REASON)) },
            ),
        )
        val outcome = useCase.accept("COT-1042") as AcceptOutcome.Refused
        assertEquals(REASON, outcome.rejection.motivo)
        assertEquals("rechazada", outcome.rejection.estado)
    }

    @Test
    fun givenARefusalTheHostCannotExplain_whenTheResultIsRead_thenItIsUnavailable() = runBlocking {
        val useCase = AcceptOffer(
            scripted(onAccept = { StandInAnswer.Failed }, onRejected = { StandInAnswer.Failed }),
        )
        assertEquals(AcceptOutcome.Unavailable, useCase.accept("COT-1042"))
    }

    @Test
    fun givenTheHostIsStillWorking_whenAccepted_thenTheCallerKeepsWaiting() = runBlocking {
        val useCase = AcceptOffer(scripted(onAccept = { StandInAnswer.Pending }))
        assertEquals(AcceptOutcome.Waiting, useCase.accept("COT-1042"))
    }
}

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class IssuanceViewModelTest {
    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenASuccessfulAccept_whenTheScreenOpens_thenTheIssuedNumberIsShown() {
        val viewModel = IssuanceViewModel(AcceptOffer(scripted(onAccept = { issued() })), "COT-1042")
        val shown = viewModel.state.value as IssuanceUi.Issued
        assertEquals("POL-88219-CO", shown.numero)
        assertEquals("Protección de dispositivo", shown.ramo)
    }

    @Test
    fun givenARefusal_whenTheScreenOpens_thenTheReasonIsShown() {
        val viewModel = IssuanceViewModel(
            AcceptOffer(
                scripted(
                    onAccept = { StandInAnswer.Failed },
                    onRejected = { StandInAnswer.Ready(IssueRejection("rechazada", REASON)) },
                ),
            ),
            "COT-1042",
        )
        val shown = viewModel.state.value as IssuanceUi.Refused
        assertEquals(REASON, shown.motivo)
    }

    @Test
    fun givenNoResultYet_whenTheScreenOpens_thenItStaysOnTheWait() {
        val pending = IssuanceViewModel(AcceptOffer(scripted(onAccept = { StandInAnswer.Pending })), "COT-1042")
        assertEquals(IssuanceUi.Waiting, pending.state.value)
        val ignored = IssuanceViewModel(
            AcceptOffer(scripted(onAccept = { StandInAnswer.Failed }, onRejected = { StandInAnswer.Failed })),
            "COT-1042",
        )
        assertEquals(IssuanceUi.Waiting, ignored.state.value)
        assertEquals(IssuanceUi.Waiting, AcceptOutcome.Ignored.toIssuanceUi())
        assertEquals(IssuanceUi.Waiting, AcceptOutcome.Waiting.toIssuanceUi())
        assertEquals(IssuanceUi.Waiting, AcceptOutcome.Unavailable.toIssuanceUi())
    }
}

private fun issued() = StandInAnswer.Ready(
    IssuedPolicy("POL-88219-CO", "Protección de dispositivo", "vigente", "2027-03-12"),
)

private fun scripted(
    onAccept: suspend () -> StandInAnswer<IssuedPolicy> = { StandInAnswer.Failed },
    onRejected: suspend () -> StandInAnswer<IssueRejection> = { StandInAnswer.Failed },
) = object : IssuanceRepository {
    override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = onAccept()

    override suspend fun rejected(): StandInAnswer<IssueRejection> = onRejected()

    override suspend fun wallet(): StandInAnswer<List<WalletEntry>> = StandInAnswer.Failed

    override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> = StandInAnswer.Failed
}
