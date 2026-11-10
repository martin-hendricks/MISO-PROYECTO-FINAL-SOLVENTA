package com.grupo8_uniandes.solventa.claim

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNoticeDraft
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticeProblems
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.PoliciesInForce
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class AvisoUiState(
    val phase: NoticePhase,
    val draft: ClaimNoticeDraft,
    val receiptId: String,
    val sendOffered: Boolean,
    val problems: NoticeProblems = NoticeProblems(),
    val rejection: String? = null,
    val sending: Boolean = false,
    val queued: Boolean = false,
    val fileRejected: Boolean = false,
    val policyOptions: List<PolicyEntry> = emptyList(),
    val policiesLoaded: Boolean = false,
    val locating: Boolean = false,
)

class AvisoSiniestroViewModel(
    private val notice: OpenClaimNotice,
    private val policiesInForce: PoliciesInForce? = null,
    private val locator: DeviceLocator? = null,
) : ViewModel() {
    private var policyOptions: List<PolicyEntry> = emptyList()
    private var policiesLoaded = false
    private var locating = false
    private var fileRejected = false
    private val _state = MutableStateFlow(notice.snapshot())
    val state: StateFlow<AvisoUiState> = _state.asStateFlow()

    init {
        val policies = policiesInForce
        if (policies != null) {
            viewModelScope.launch {
                val options = policies()
                policyOptions = options
                policiesLoaded = true
                if (options.isNotEmpty()) notice.offerPolicies(options.map { it.numero })
                publish()
            }
        }
    }

    fun reopen() {
        notice.reopen()
        publish()
    }

    fun continueToEvidence(): Boolean {
        notice.continueToEvidence()
        publish()
        return notice.phase == NoticePhase.Evidence
    }

    fun revise(poliza: String, fechaHecho: String, descripcion: String, lugar: String) {
        notice.revise(poliza, fechaHecho, descripcion, lugar)
        publish()
    }

    fun toggleGeotag(on: Boolean) {
        notice.setGeotag(on)
        publish()
    }

    fun useCurrentLocation() {
        val locator = locator ?: return
        viewModelScope.launch {
            locating = true
            publish()
            notice.placeAt(locator.current())
            locating = false
            publish()
        }
    }

    fun denyCurrentLocation() {
        notice.placeAt(null)
        publish()
    }

    fun markCameraDenied() {
        notice.markCameraDenied()
        publish()
    }

    fun attach(attachment: Attachment, bytes: ByteArray? = null): Boolean {
        val accepted = notice.attachFile(attachment, bytes)
        fileRejected = !accepted
        publish()
        return accepted
    }

    fun remove(nombre: String) {
        notice.remove(nombre)
        fileRejected = false
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
        problems = problems(),
        rejection = rejection,
        sending = sending,
        queued = queued,
        fileRejected = fileRejected,
        policyOptions = policyOptions,
        policiesLoaded = policiesLoaded,
        locating = locating,
    )
}
