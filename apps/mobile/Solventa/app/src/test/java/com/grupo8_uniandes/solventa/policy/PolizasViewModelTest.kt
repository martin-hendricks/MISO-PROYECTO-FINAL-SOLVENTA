package com.grupo8_uniandes.solventa.policy

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssueRejection
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuedPolicy
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.ui.shell.PolizasScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class PolizasViewModelTest {
    @get:Rule
    val rule = createComposeRule()

    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenAWalletRow_whenOpened_thenItsNumeroIsPassedThrough() {
        val opened = mutableListOf<String>()
        rule.setContent {
            SolventaTheme {
                PolizasScreen(
                    policies = listOf(publishedRow()),
                    onOpenPolicy = { opened += it },
                    onNewQuote = {},
                )
            }
        }
        rule.onNodeWithTag("action_open_policy_POL-88219-CO").performClick()
        assertEquals(listOf("POL-88219-CO"), opened)
    }

    @Test
    fun givenAFailedWallet_whenShown_thenSol0001IsAbsent() {
        val viewModel = PolizasViewModel(scripted(wallet = StandInAnswer.Failed))
        assertEquals(WalletPhase.Failed, viewModel.state.value.phase)
        assertTrue(viewModel.state.value.policies.isEmpty())

        rule.setContent {
            SolventaTheme {
                PolizasScreen(
                    policies = viewModel.state.value.policies,
                    failed = viewModel.state.value.phase == WalletPhase.Failed,
                    onOpenPolicy = {},
                    onNewQuote = {},
                )
            }
        }
        rule.onAllNodesWithText("SOL-0001").assertCountEquals(0)
        rule.onAllNodesWithText("POL-88219-CO").assertCountEquals(0)
        rule.onNodeWithText("No se pudo cargar la información.").assertIsDisplayed()
    }

    @Test
    fun givenLoadedRows_whenALaterRefreshFails_thenTheRowsStay() {
        var answer: StandInAnswer<List<WalletEntry>> = StandInAnswer.Ready(listOf(publishedRow()))
        val viewModel = PolizasViewModel(
            object : IssuanceRepository {
                override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = StandInAnswer.Failed

                override suspend fun rejected(): StandInAnswer<IssueRejection> = StandInAnswer.Failed

                override suspend fun wallet(): StandInAnswer<List<WalletEntry>> = answer

                override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> = StandInAnswer.Failed
            },
        )
        assertEquals(WalletPhase.Ready, viewModel.state.value.phase)
        answer = StandInAnswer.Failed

        viewModel.refresh()

        assertEquals(WalletPhase.Failed, viewModel.state.value.phase)
        assertEquals("POL-88219-CO", viewModel.state.value.policies.single().numero)
    }

    @Test
    fun givenALoadInFlight_whenRefreshAgain_thenTheFirstCallFinishes() {
        val gate = CompletableDeferred<StandInAnswer<List<WalletEntry>>>()
        var calls = 0
        val viewModel = PolizasViewModel(
            object : IssuanceRepository {
                override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = StandInAnswer.Failed

                override suspend fun rejected(): StandInAnswer<IssueRejection> = StandInAnswer.Failed

                override suspend fun wallet(): StandInAnswer<List<WalletEntry>> {
                    calls += 1
                    return gate.await()
                }

                override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> = StandInAnswer.Failed
            },
        )
        assertEquals(1, calls)

        viewModel.refresh()

        assertEquals(1, calls)
        gate.complete(StandInAnswer.Ready(listOf(publishedRow())))
        assertEquals(WalletPhase.Ready, viewModel.state.value.phase)
        assertEquals("POL-88219-CO", viewModel.state.value.policies.single().numero)
    }

    @Test
    fun givenAPendingWallet_whenItLoads_thenTheListStaysEmpty() {
        val viewModel = PolizasViewModel(scripted(wallet = StandInAnswer.Pending))

        assertEquals(WalletPhase.Pending, viewModel.state.value.phase)
        assertTrue(viewModel.state.value.policies.isEmpty())
    }

    @Test
    fun givenAPolicyNumber_whenDetailIsPendingOrFailed_thenTheNumberStays() {
        val pending = PolizaDetalleViewModel(scripted(detail = StandInAnswer.Pending), "POL-9")
        assertEquals(PolicyPhase.Pending, pending.state.value.phase)
        assertEquals("POL-9", pending.state.value.numero)

        val failed = PolizaDetalleViewModel(scripted(detail = StandInAnswer.Failed), "POL-9")
        assertEquals(PolicyPhase.Failed, failed.state.value.phase)
        assertEquals("POL-9", failed.state.value.numero)
        assertEquals("", failed.state.value.queHacer)
    }

    @Test
    fun givenAPolicyNumber_whenDetailLoads_thenThatNumberIsRequested() {
        val repository = scripted(
            detail = StandInAnswer.Ready(
                PolicyDetail(
                    numero = "POL-88219-CO",
                    ramo = "Protección de dispositivo",
                    resumen = "Robo, Pantalla, Hurto",
                    estado = "vigente",
                    venceEn = "2027-03-12",
                    queHacer = "Toma la foto del daño y anota fecha y lugar.",
                ),
            ),
        )
        val viewModel = PolizaDetalleViewModel(repository, "POL-88219-CO")
        assertEquals("POL-88219-CO", repository.asked)
        assertEquals(PolicyPhase.Ready, viewModel.state.value.phase)
        assertEquals("POL-88219-CO", viewModel.state.value.numero)
        assertEquals("Toma la foto del daño y anota fecha y lugar.", viewModel.state.value.queHacer)
    }

    private fun publishedRow() = WalletEntry(
        numero = "POL-88219-CO",
        ramo = "Protección de dispositivo",
        resumen = "Robo, Pantalla, Hurto",
        estado = "vigente",
        venceEn = "2027-03-12",
    )

    private fun scripted(
        wallet: StandInAnswer<List<WalletEntry>> = StandInAnswer.Failed,
        detail: StandInAnswer<PolicyDetail> = StandInAnswer.Failed,
    ) = object : IssuanceRepository {
        var asked: String? = null

        override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = StandInAnswer.Failed

        override suspend fun rejected(): StandInAnswer<IssueRejection> = StandInAnswer.Failed

        override suspend fun wallet(): StandInAnswer<List<WalletEntry>> = wallet

        override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> {
            asked = numero
            return detail
        }
    }
}
