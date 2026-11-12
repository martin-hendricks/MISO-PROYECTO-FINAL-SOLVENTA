package com.grupo8_uniandes.solventa.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.MemoryClaimHold
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.PoliciesInForce
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssueRejection
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuedPolicy
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AvisoSiniestroViewModelTest {
    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenTheForm_whenTheCustomerMovesThroughTheNotice_thenTheViewModelFollowsTheUseCase() {
        val notice = OpenClaimNotice(QuietClaims(), MemoryClaimHold()) { "key-1" }
        val viewModel = AvisoSiniestroViewModel(
            notice,
            locator = FixedLocator(GeoPoint(4.65, -74.08, 8)),
        )

        val sample = com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNoticeDraft.Review
        viewModel.revise(sample.poliza, sample.fechaHecho, sample.descripcion, sample.lugar)
        viewModel.continueToEvidence()
        assertEquals(NoticePhase.Evidence, viewModel.state.value.phase)
        viewModel.toggleGeotag(true)
        viewModel.useCurrentLocation()
        assertEquals(4.65, viewModel.state.value.draft.geo!!.lat, 0.001)
        assertFalse(viewModel.state.value.locating)
        viewModel.toggleGeotag(false)
        assertEquals(null, viewModel.state.value.draft.geo)
        viewModel.denyCurrentLocation()
        assertTrue(viewModel.state.value.draft.locationDenied)
        viewModel.markCameraDenied()
        assertTrue(viewModel.state.value.draft.cameraDenied)
        assertTrue(
            viewModel.attach(Attachment(AttachmentKind.FOTO, "foto.jpg", "image/jpeg", 4), byteArrayOf(1, 2, 3, 4)),
        )
        viewModel.remove("foto.jpg")
        assertTrue(viewModel.state.value.draft.adjuntos.isEmpty())
        viewModel.attach(Attachment(AttachmentKind.FOTO, "foto.jpg", "image/jpeg", 4), byteArrayOf(1, 2, 3, 4))
        viewModel.queue()
        assertEquals("", viewModel.state.value.receiptId)
        assertTrue(viewModel.state.value.queued)
        assertFalse(viewModel.state.value.phase == NoticePhase.Confirmation)

        viewModel.send()
        assertEquals("SIN-441", viewModel.state.value.receiptId)
        assertEquals(NoticePhase.Confirmation, viewModel.state.value.phase)

        viewModel.cancel()
        assertEquals(NoticePhase.Closed, viewModel.state.value.phase)
        viewModel.reopen()
        assertEquals(NoticePhase.Form, viewModel.state.value.phase)
        assertEquals("", viewModel.state.value.receiptId)
    }

    @Test
    fun givenOnePolicyInForce_whenTheFormOpens_thenItIsPreselected() = runBlocking {
        val wallet = ScriptedWallet()
        assertEquals(listOf("POL-1", "POL-3", "POL-5"), PoliciesInForce(wallet).invoke().map { it.numero })
        assertEquals("Vida", PoliciesInForce(wallet).invoke()[1].ramo)
        wallet.fail = true
        assertEquals(emptyList<WalletEntry>(), PoliciesInForce(wallet).invoke())
        val viewModel = AvisoSiniestroViewModel(
            OpenClaimNotice(QuietClaims(), MemoryClaimHold()) { "key-1" },
            PoliciesInForce(ScriptedWallet(onlyOne = true)),
            FixedLocator(null),
        )
        assertEquals(listOf("POL-1"), viewModel.state.value.policyOptions.map { it.numero })
        assertTrue(viewModel.state.value.policiesLoaded)
        viewModel.useCurrentLocation()
        assertTrue(viewModel.state.value.draft.locationDenied)
        assertEquals("POL-1", viewModel.state.value.draft.poliza)
        viewModel.revise("POL-1", "2026-11-01", "Choque", "Calle 72")
        assertEquals("Calle 72", viewModel.state.value.draft.lugar)
        assertFalse(
            viewModel.attach(
                com.grupo8_uniandes.solventa.domain.bff.claim.Attachment(
                    com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind.FOTO,
                    "a.exe",
                    "application/x-msdownload",
                    10,
                ),
            ),
        )
        assertTrue(viewModel.state.value.fileRejected)
        assertEquals(false, AvisoUiState(NoticePhase.Form, viewModel.state.value.draft, "", false).queued)
    }

    private class ScriptedWallet(
        var fail: Boolean = false,
        private val onlyOne: Boolean = false,
    ) : IssuanceRepository {
        override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> = StandInAnswer.Failed
        override suspend fun rejected(): StandInAnswer<IssueRejection> = StandInAnswer.Failed
        override suspend fun wallet(): StandInAnswer<List<WalletEntry>> = if (fail) {
            StandInAnswer.Failed
        } else {
            StandInAnswer.Ready(
                if (onlyOne) {
                    listOf(WalletEntry("POL-1", "SOAT", "moto", "vigente", "2027-01-01"))
                } else {
                    listOf(
                        WalletEntry("POL-1", "SOAT", "moto", "vigente", "2027-01-01"),
                        WalletEntry("POL-2", "SOAT", "moto", "vencida", "2020-01-01"),
                        WalletEntry("POL-3", "Vida", "amparo", "por_vencer", "2026-12-01"),
                        WalletEntry("POL-4", "SOAT", "moto", "cancelada", "2027-01-01"),
                        WalletEntry("POL-5", "SOAT", "moto", "VIGENTE", "2027-06-01"),
                        WalletEntry("POL-6", "SOAT", "moto", "CANCELADA", "2027-06-01"),
                    )
                },
            )
        }
        override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> = StandInAnswer.Failed
    }

    private class FixedLocator(private val point: GeoPoint?) : DeviceLocator {
        override suspend fun current(): GeoPoint? = point
    }

    private class QuietClaims : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> =
            StandInAnswer.Ready(ClaimReceipt("SIN-441", ClaimStatus.EN_EVALUACION))

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Failed
    }
}
