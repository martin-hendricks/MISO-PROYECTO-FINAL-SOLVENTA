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
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyCancellation
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyCoverage
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import com.grupo8_uniandes.solventa.ui.shell.PolizaDetalleScreen
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
        assertEquals(PoliciesPhase.Failed, viewModel.state.value.phase)
        assertTrue(viewModel.state.value.policies.isEmpty())

        rule.setContent {
            SolventaTheme {
                PolizasScreen(
                    policies = viewModel.state.value.policies,
                    phase = viewModel.state.value.phase,
                    onOpenPolicy = {},
                    onNewQuote = {},
                )
            }
        }
        rule.onAllNodesWithText("SOL-0001").assertCountEquals(0)
        rule.onAllNodesWithText("POL-88219-CO").assertCountEquals(0)
        rule.onNodeWithText("¿Aún no tienes pólizas? Puedes pedir tu primera cotización aquí mismo.").assertIsDisplayed()
    }

    @Test
    fun givenAnEmptyList_whenThePromptIsUsed_thenTheQuoteOpensAndAPendingListStaysBlank() {
        var quotes = 0
        rule.setContent {
            SolventaTheme {
                PolizasScreen(
                    policies = emptyList(),
                    onOpenPolicy = {},
                    onNewQuote = { quotes += 1 },
                    notice = true,
                )
            }
        }
        rule.onNodeWithTag("action_request_quote").performClick()
        rule.onNodeWithTag("policy_sync_notice").assertIsDisplayed()
        assertEquals(1, quotes)
    }

    @Test
    fun givenAPendingList_whenShown_thenTheEmptyPromptStaysHidden() {
        rule.setContent {
            SolventaTheme {
                PolizasScreen(
                    policies = emptyList(),
                    phase = PoliciesPhase.Pending,
                    onOpenPolicy = {},
                    onNewQuote = {},
                )
            }
        }
        rule.onAllNodesWithText("Solicitar cotización").assertCountEquals(0)
    }

    @Test
    fun givenAReadyDetail_whenShown_thenGuidanceAndTheNoticeStayOnThisScreen() {
        assertEquals("", PolicyDetailUiState().queHacer)
        var notices = 0
        rule.setContent {
            SolventaTheme {
                PolizaDetalleScreen(
                    state = PolicyDetailUiState(
                        phase = PolicyPhase.Ready,
                        detail = PolicyDetail(
                            numero = "POL-88219-CO",
                            ramo = "Protección de dispositivo",
                            resumen = "Robo y Pantalla",
                            estado = "vigente",
                            venceEn = "2027-03-12",
                            queHacer = "Toma la foto del daño y anota fecha y lugar.",
                            inicioVigencia = "2026-03-12",
                            finVigencia = "2027-03-12",
                            moneda = "COP",
                            primaTotal = 89000.0,
                            coberturas = listOf(
                                PolicyCoverage("Robo", 4_000_000.0, 0.0),
                                PolicyCoverage("Pantalla", 1_500_000.0, 150_000.0),
                            ),
                            renovable = true,
                        ),
                        notice = true,
                        claims = listOf(
                            ClaimSummary("SIN-1", "SOAT", "choque", ClaimStatus.RECIBIDO, poliza = "POL-88219-CO"),
                        ),
                    ),
                    renewalChecked = true,
                    onExpiryNotices = { notices += 1 },
                )
            }
        }
        rule.onNodeWithTag("policy_guidance", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("policy_vigencia", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("policy_prima", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("policy_coverage_Robo", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("policy_deductible_Pantalla", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("renewal_checkbox", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("policy_claim_SIN-1", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("policy_sync_notice", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("action_expiry_notices").performClick()
        assertEquals(1, notices)
    }

    @Test
    fun givenACancelledPolicy_whenShown_thenTheRefundAndTheEmptyClaimsStay() {
        var opened = ""
        var reported = 0
        rule.setContent {
            SolventaTheme {
                PolizaDetalleScreen(
                    state = PolicyDetailUiState(
                        phase = PolicyPhase.Ready,
                        detail = PolicyDetail(
                            numero = "POL-9",
                            ramo = "SOAT motocicleta",
                            resumen = "Sin coberturas detalladas",
                            estado = "CANCELADA",
                            venceEn = "no-es-fecha",
                            queHacer = "",
                            inicioVigencia = "   ",
                            finVigencia = null,
                            moneda = "",
                            primaTotal = null,
                            coberturas = emptyList(),
                            renovable = false,
                            cancelacion = PolicyCancellation(
                                motivo = "Fin del contrato",
                                canceladaEn = "2026-11-01",
                                devolucionEstimada = 12_000.0,
                            ),
                        ),
                        claims = emptyList(),
                    ),
                    onOpenClaim = { opened = it },
                    onReportClaim = { reported += 1 },
                )
            }
        }
        rule.onNodeWithText("Sin coberturas detalladas", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithText("Cancelada", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithText("Fin del contrato", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("policy_refund", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("policy_claims_empty").assertIsDisplayed()
        rule.onNodeWithTag("action_report_claim").performClick()
        assertEquals(1, reported)
        assertEquals("", opened)
    }

    @Test
    fun givenOnlyAnEndDate_whenShown_thenThatDateIsTheVigencia() {
        rule.setContent {
            SolventaTheme {
                PolizaDetalleScreen(
                    state = PolicyDetailUiState(
                        phase = PolicyPhase.Ready,
                        detail = PolicyDetail(
                            numero = "POL-2",
                            ramo = "Vida",
                            resumen = "x",
                            estado = "por_vencer",
                            venceEn = "",
                            queHacer = "",
                            inicioVigencia = null,
                            finVigencia = "2027-01-01",
                            moneda = "MXN",
                            primaTotal = 10.0,
                            coberturas = listOf(PolicyCoverage("Vida", 1.0, 0.0)),
                            cancelacion = PolicyCancellation("  ", "", null),
                        ),
                    ),
                )
            }
        }
        rule.onNodeWithTag("policy_vigencia", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithText("Por vencer", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithTag("policy_prima", useUnmergedTree = true).assertIsDisplayed()
    }

    @Test
    fun givenNoDatesAndAnUnknownStatus_whenShown_thenTheRawStatusStays() {
        rule.setContent {
            SolventaTheme {
                PolizaDetalleScreen(
                    state = PolicyDetailUiState(
                        phase = PolicyPhase.Ready,
                        requested = "POL-3",
                        detail = PolicyDetail(
                            numero = "POL-3",
                            ramo = "Vida",
                            resumen = "Sin fechas",
                            estado = "suspendida",
                            venceEn = " ",
                            queHacer = "",
                            inicioVigencia = "",
                            finVigencia = null,
                        ),
                    ),
                )
            }
        }
        rule.onNodeWithText("suspendida", useUnmergedTree = true).assertIsDisplayed()
        rule.onNodeWithText("Sin fechas", useUnmergedTree = true).assertIsDisplayed()
    }

    @Test
    fun givenOnlyAStartDate_whenShown_thenTheVigenciaStaysEmpty() {
        var opened = ""
        rule.setContent {
            SolventaTheme {
                PolizaDetalleScreen(
                    state = PolicyDetailUiState(
                        phase = PolicyPhase.Ready,
                        detail = PolicyDetail(
                            numero = "POL-4",
                            ramo = "Vida",
                            resumen = "Inicio",
                            estado = "vigente",
                            venceEn = " ",
                            queHacer = "",
                            inicioVigencia = "2026-03-12",
                            finVigencia = null,
                            cancelacion = PolicyCancellation("no", "2026-01-01", 1.0),
                        ),
                        claims = listOf(
                            ClaimSummary("SIN-4", "Vida", "hecho", ClaimStatus.RECIBIDO),
                        ),
                    ),
                    onOpenClaim = { opened = it },
                )
            }
        }
        rule.onNodeWithTag("policy_claim_SIN-4", useUnmergedTree = true).performClick()
        assertEquals("SIN-4", opened)
    }

    @Test
    fun givenLoadedRows_whenALaterRefreshFails_thenTheRowsStay() {
        var answer: StandInAnswer<List<PolicyEntry>> = StandInAnswer.Ready(listOf(publishedRow()))
        val viewModel = PolizasViewModel(
            object : IssuanceRepository {
                override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = StandInAnswer.Failed

                override suspend fun rejected(): StandInAnswer<IssueRejection> = StandInAnswer.Failed

                override suspend fun policies(): StandInAnswer<List<PolicyEntry>> = answer

                override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> = StandInAnswer.Failed
            },
        )
        assertEquals(PoliciesPhase.Ready, viewModel.state.value.phase)
        answer = StandInAnswer.Failed

        viewModel.refresh()

        assertEquals(PoliciesPhase.Ready, viewModel.state.value.phase)
        assertEquals("POL-88219-CO", viewModel.state.value.policies.single().numero)
    }

    @Test
    fun givenALoadInFlight_whenRefreshAgain_thenTheFirstCallFinishes() {
        val gate = CompletableDeferred<StandInAnswer<List<PolicyEntry>>>()
        var calls = 0
        val viewModel = PolizasViewModel(
            object : IssuanceRepository {
                override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = StandInAnswer.Failed

                override suspend fun rejected(): StandInAnswer<IssueRejection> = StandInAnswer.Failed

                override suspend fun policies(): StandInAnswer<List<PolicyEntry>> {
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
        assertEquals(PoliciesPhase.Ready, viewModel.state.value.phase)
        assertEquals("POL-88219-CO", viewModel.state.value.policies.single().numero)
    }

    @Test
    fun givenAPendingWallet_whenItLoads_thenTheListStaysEmpty() {
        val viewModel = PolizasViewModel(scripted(wallet = StandInAnswer.Pending))

        assertEquals(PoliciesPhase.Pending, viewModel.state.value.phase)
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

    private fun publishedRow() = PolicyEntry(
        numero = "POL-88219-CO",
        ramo = "Protección de dispositivo",
        resumen = "Robo, Pantalla, Hurto",
        estado = "vigente",
        venceEn = "2027-03-12",
    )

    private fun scripted(
        wallet: StandInAnswer<List<PolicyEntry>> = StandInAnswer.Failed,
        detail: StandInAnswer<PolicyDetail> = StandInAnswer.Failed,
    ) = object : IssuanceRepository {
        var asked: String? = null

        override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = StandInAnswer.Failed

        override suspend fun rejected(): StandInAnswer<IssueRejection> = StandInAnswer.Failed

        override suspend fun policies(): StandInAnswer<List<PolicyEntry>> = wallet

        override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> {
            asked = numero
            return detail
        }
    }
}
