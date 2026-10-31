package com.grupo8_uniandes.solventa.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.MemoryClaimHold
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
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
        val viewModel = AvisoSiniestroViewModel(OpenClaimNotice(QuietClaims(), MemoryClaimHold()) { "key-1" })

        viewModel.continueToCamera()
        assertEquals(NoticePhase.Camera, viewModel.state.value.phase)
        viewModel.dismissCamera()
        viewModel.allowCamera()
        viewModel.attachVideo()
        viewModel.attachReceipt()
        viewModel.attachSupport()
        viewModel.openLocation()
        viewModel.dismissLocation()
        viewModel.allowLocation()
        viewModel.denyLocation()
        viewModel.denyCamera()
        viewModel.choosePhotos()
        viewModel.denyPhotos()
        viewModel.choosePhotos()
        viewModel.allowPhotos()
        viewModel.queue()
        assertEquals("", viewModel.state.value.receiptId)
        assertFalse(viewModel.state.value.sendOffered && viewModel.state.value.phase == NoticePhase.Confirmation)

        viewModel.send()
        assertEquals("SIN-441", viewModel.state.value.receiptId)
        assertEquals(NoticePhase.Confirmation, viewModel.state.value.phase)

        viewModel.cancel()
        assertEquals(NoticePhase.Closed, viewModel.state.value.phase)
        viewModel.reopen()
        assertEquals(NoticePhase.Form, viewModel.state.value.phase)
        assertEquals("", viewModel.state.value.receiptId)
    }

    private class QuietClaims : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice, idempotencyKey: String?): StandInAnswer<ClaimReceipt> =
            StandInAnswer.Ready(ClaimReceipt("SIN-441", ClaimStatus.EN_EVALUACION))

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Failed
    }
}
