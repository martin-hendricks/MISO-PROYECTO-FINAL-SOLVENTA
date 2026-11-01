package com.grupo8_uniandes.solventa.claim

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.ui.shell.SiniestrosScreen
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
class SiniestrosViewModelTest {
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
    fun givenAClaimRow_whenOpened_thenItsIdIsPassedThrough() {
        val opened = mutableListOf<String>()
        rule.setContent {
            SolventaTheme {
                SiniestrosScreen(
                    claims = listOf(publishedRow()),
                    onOpenClaim = { opened += it },
                    onOpenCatalog = {},
                )
            }
        }
        rule.onNodeWithTag("action_open_claim_SIN-441").performClick()
        assertEquals(listOf("SIN-441"), opened)
    }

    @Test
    fun givenAPendingList_whenItLoads_thenNoClaimIsShown() {
        val viewModel = SiniestrosViewModel(scripted(StandInAnswer.Pending))

        assertEquals(ClaimsPhase.Pending, viewModel.state.value.phase)
        assertTrue(viewModel.state.value.claims.isEmpty())
    }

    @Test
    fun givenAFailedList_whenShown_thenNoIdIsInvented() {
        val viewModel = SiniestrosViewModel(scripted(StandInAnswer.Failed))
        assertEquals(ClaimsPhase.Failed, viewModel.state.value.phase)
        assertTrue(viewModel.state.value.claims.isEmpty())

        rule.setContent {
            SolventaTheme {
                SiniestrosScreen(
                    claims = viewModel.state.value.claims,
                    failed = viewModel.state.value.phase == ClaimsPhase.Failed,
                    onOpenClaim = {},
                    onOpenCatalog = {},
                )
            }
        }
        rule.onAllNodesWithText("SIN-441").assertCountEquals(0)
        rule.onNodeWithText("No se pudo cargar la información.").assertIsDisplayed()
    }

    @Test
    fun givenLoadedRows_whenALaterRefreshFails_thenTheRowsStay() {
        var answer: StandInAnswer<List<ClaimSummary>> = StandInAnswer.Ready(listOf(publishedRow()))
        val viewModel = SiniestrosViewModel(
            object : ClaimRepository {
                override suspend fun notify(notice: ClaimNotice): StandInAnswer<ClaimReceipt> = StandInAnswer.Failed

                override suspend fun list(): StandInAnswer<List<ClaimSummary>> = answer
            },
        )
        assertEquals(ClaimsPhase.Ready, viewModel.state.value.phase)
        answer = StandInAnswer.Failed

        viewModel.refresh()

        assertEquals(ClaimsPhase.Failed, viewModel.state.value.phase)
        assertEquals("SIN-441", viewModel.state.value.claims.single().siniestroId)
    }

    @Test
    fun givenALoadInFlight_whenRefreshAgain_thenTheFirstCallFinishes() {
        val gate = CompletableDeferred<StandInAnswer<List<ClaimSummary>>>()
        var calls = 0
        val viewModel = SiniestrosViewModel(
            object : ClaimRepository {
                override suspend fun notify(notice: ClaimNotice): StandInAnswer<ClaimReceipt> = StandInAnswer.Failed

                override suspend fun list(): StandInAnswer<List<ClaimSummary>> {
                    calls += 1
                    return gate.await()
                }
            },
        )
        assertEquals(1, calls)

        viewModel.refresh()

        assertEquals(1, calls)
        gate.complete(StandInAnswer.Ready(listOf(publishedRow())))
        assertEquals(ClaimsPhase.Ready, viewModel.state.value.phase)
        assertEquals("SIN-441", viewModel.state.value.claims.single().siniestroId)
    }

    @Test
    fun givenTheReviewSet_whenLoaded_thenEachClaimKeepsItsStatusWords() {
        val viewModel = SiniestrosViewModel(scripted(StandInAnswer.Ready(reviewRows())))

        assertEquals(ClaimsPhase.Ready, viewModel.state.value.phase)
        assertEquals(listOf("SIN-441", "SIN-220", "SIN-P01"), viewModel.state.value.claims.map { it.siniestroId })
        assertEquals("En evaluación", viewModel.state.value.claims[0].statusWords())
        assertEquals("Pagado", viewModel.state.value.claims[1].statusWords())
        assertEquals("Pago automático · pagado", viewModel.state.value.claims[2].statusWords())
        viewModel.openClaim("SIN-441")
        assertEquals("SIN-441", viewModel.state.value.openedClaimId)
    }

    private fun reviewRows() = listOf(
        ClaimSummary("SIN-441", "Protección de dispositivo", "pantalla rota", ClaimStatus.EN_EVALUACION),
        ClaimSummary("SIN-220", "Protección de dispositivo", "hurto", ClaimStatus.PAGADO),
        ClaimSummary(
            "SIN-P01",
            "Clima y vuelos",
            "retraso de vuelo",
            ClaimStatus.PAGADO,
            estadoTexto = "Pago automático · pagado",
        ),
    )

    private fun publishedRow() = ClaimSummary(
        siniestroId = "SIN-441",
        ramo = "Protección de dispositivo",
        resumen = "Pantalla rota",
        estado = ClaimStatus.EN_EVALUACION,
    )

    private fun scripted(answer: StandInAnswer<List<ClaimSummary>>) = object : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice): StandInAnswer<ClaimReceipt> = StandInAnswer.Failed

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = answer
    }
}
