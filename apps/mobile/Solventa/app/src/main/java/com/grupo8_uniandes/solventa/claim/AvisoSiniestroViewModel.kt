package com.grupo8_uniandes.solventa.claim

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNoticeDraft
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class AvisoUiState(
    val phase: NoticePhase,
    val draft: ClaimNoticeDraft,
    val receiptId: String,
    val sendOffered: Boolean,
)

class AvisoSiniestroViewModel(
    private val notice: OpenClaimNotice,
) : ViewModel() {
    private val _state = MutableStateFlow(notice.snapshot())
    val state: StateFlow<AvisoUiState> = _state.asStateFlow()

    fun reopen() {
        notice.reopen()
        publish()
    }

    fun continueToCamera() {
        notice.continueToCamera()
        publish()
    }

    fun allowCamera() {
        notice.allowCamera()
        publish()
    }

    fun denyCamera() {
        notice.denyCamera()
        publish()
    }

    fun dismissCamera() {
        notice.dismissCamera()
        publish()
    }

    fun choosePhotos() {
        notice.choosePhotos()
        publish()
    }

    fun allowPhotos() {
        notice.allowPhotos()
        publish()
    }

    fun denyPhotos() {
        notice.denyPhotos()
        publish()
    }

    fun attachVideo() {
        notice.attachVideo()
        publish()
    }

    fun attachReceipt() {
        notice.attachReceipt()
        publish()
    }

    fun attachSupport() {
        notice.attachSupport()
        publish()
    }

    fun openLocation() {
        notice.openLocation()
        publish()
    }

    fun allowLocation() {
        notice.allowLocation()
        publish()
    }

    fun denyLocation() {
        notice.denyLocation()
        publish()
    }

    fun dismissLocation() {
        notice.dismissLocation()
        publish()
    }

    fun queue() {
        notice.queue()
        publish()
    }

    fun send() {
        viewModelScope.launch {
            notice.send()
            publish()
        }
    }

    fun cancel() {
        notice.cancel()
        publish()
    }

    private fun publish() {
        _state.value = notice.snapshot()
    }

    private fun OpenClaimNotice.snapshot() = AvisoUiState(
        phase = phase,
        draft = draft,
        receiptId = receipt?.siniestroId.orEmpty(),
        sendOffered = sendOffered(),
    )
}
