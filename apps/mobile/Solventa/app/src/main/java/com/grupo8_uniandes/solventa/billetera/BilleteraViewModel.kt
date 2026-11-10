package com.grupo8_uniandes.solventa.billetera

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.billetera.Deposit
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositMemory
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositRepository
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositType
import com.grupo8_uniandes.solventa.domain.bff.billetera.ListDeposits
import com.grupo8_uniandes.solventa.domain.bff.billetera.Wallet
import com.grupo8_uniandes.solventa.domain.bff.billetera.WalletNotice
import com.grupo8_uniandes.solventa.domain.bff.billetera.WalletSource
import com.grupo8_uniandes.solventa.domain.bff.billetera.changed
import com.grupo8_uniandes.solventa.domain.network.NetworkMonitor
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class WalletPhase { Loading, Ready, Empty, Error, FirstLoad }

data class BilleteraUiState(
    val phase: WalletPhase = WalletPhase.Loading,
    val wallet: Wallet? = null,
    val chip: DepositType? = null,
    val source: WalletSource? = null,
    val notice: WalletNotice = WalletNotice.None,
    val savedAt: String? = null,
    val offline: Boolean = false,
) {
    val visible: List<Deposit>
        get() = wallet?.movimientos?.filter { chip == null || it.tipo == chip }.orEmpty()
}

class BilleteraViewModel(
    private val deposits: ListDeposits,
    network: NetworkMonitor,
) : ViewModel() {
    private val stateFlow = MutableStateFlow(BilleteraUiState())
    val state: StateFlow<BilleteraUiState> = stateFlow.asStateFlow()
    var reads: Int = 0
        private set
    private var online = network.online.value

    init {
        viewModelScope.launch {
            network.online.collect { now ->
                val rising = !online && now
                online = now
                stateFlow.value = stateFlow.value.copy(offline = !now)
                val showingCopy = stateFlow.value.source == WalletSource.Copy
                if (rising && showingCopy) refresh(announce = true)
                else if (stateFlow.value.phase == WalletPhase.Loading) refresh(announce = false)
            }
        }
    }

    fun refresh(announce: Boolean = false) {
        viewModelScope.launch {
            val previous = stateFlow.value.wallet
            reads += 1
            val read = deposits()
            val updated = announce &&
                previous != null &&
                read.wallet != null &&
                read.source == WalletSource.Fresh &&
                changed(previous, read.wallet)
            stateFlow.value = stateFlow.value.copy(
                phase = when (read.notice) {
                    WalletNotice.NeedsFirstLoad -> WalletPhase.FirstLoad
                    else -> when {
                        read.wallet == null -> WalletPhase.Error
                        read.wallet.movimientos.isEmpty() -> WalletPhase.Empty
                        else -> WalletPhase.Ready
                    }
                },
                wallet = read.wallet,
                source = read.source,
                notice = if (updated) WalletNotice.Updated else read.notice,
                savedAt = read.savedAt,
                offline = !online,
            )
        }
    }

    fun select(chip: DepositType?) {
        stateFlow.value = stateFlow.value.copy(chip = chip)
    }

    fun newest(): Deposit? = stateFlow.value.wallet?.movimientos?.maxByOrNull { it.depositadoEn }
}

enum class DepositPhase { Loading, Ready, Missing, Error, FirstLoad }

data class DepositoUiState(
    val phase: DepositPhase = DepositPhase.Loading,
    val deposit: Deposit? = null,
    val offline: Boolean = false,
    val notice: WalletNotice = WalletNotice.None,
    val savedAt: String? = null,
    val needsNetwork: Boolean = false,
) {
    val downloadEnabled: Boolean get() = deposit != null && !offline
}

class DepositoViewModel(
    private val id: String,
    private val repository: DepositRepository,
    private val memory: DepositMemory,
    network: NetworkMonitor,
) : ViewModel() {
    private val stateFlow = MutableStateFlow(DepositoUiState())
    val state: StateFlow<DepositoUiState> = stateFlow.asStateFlow()
    private var online = network.online.value

    init {
        viewModelScope.launch {
            network.online.collect { now ->
                val rising = !online && now
                online = now
                stateFlow.value = stateFlow.value.copy(offline = !now)
                if (stateFlow.value.phase == DepositPhase.Loading || (rising && stateFlow.value.notice == WalletNotice.Offline)) {
                    load()
                }
            }
        }
    }

    fun load() {
        viewModelScope.launch {
            val previous = stateFlow.value.deposit
            when (val answer = repository.deposit(id)) {
                is StandInAnswer.Ready -> stateFlow.value = DepositoUiState(
                    phase = DepositPhase.Ready,
                    deposit = answer.value,
                    offline = !online,
                    notice = if (previous != null && previous.comprobante != answer.value.comprobante) {
                        WalletNotice.Updated
                    } else {
                        WalletNotice.None
                    },
                )
                is StandInAnswer.Rejected -> stateFlow.value = DepositoUiState(
                    phase = DepositPhase.Missing,
                    offline = !online,
                )
                StandInAnswer.Failed, StandInAnswer.Pending -> fromCopy()
            }
        }
    }

    fun openClaim(): String? {
        val deposit = stateFlow.value.deposit ?: return null
        if (!online) {
            stateFlow.value = stateFlow.value.copy(needsNetwork = true)
            return null
        }
        return deposit.id
    }

    private fun fromCopy() {
        val stored = memory.read()?.wallet?.movimientos?.firstOrNull { it.id == id }
        if (stored == null) {
            stateFlow.value = DepositoUiState(phase = DepositPhase.FirstLoad, offline = !online, notice = WalletNotice.NeedsFirstLoad)
        } else {
            val savedAt = memory.read()?.savedAt
            stateFlow.value = DepositoUiState(
                phase = DepositPhase.Ready,
                deposit = stored,
                offline = !online,
                notice = WalletNotice.Offline,
                savedAt = savedAt,
            )
        }
    }
}
