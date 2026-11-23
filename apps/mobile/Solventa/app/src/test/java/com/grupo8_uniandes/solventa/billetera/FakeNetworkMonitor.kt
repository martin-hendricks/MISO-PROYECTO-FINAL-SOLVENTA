package com.grupo8_uniandes.solventa.billetera

import com.grupo8_uniandes.solventa.domain.network.NetworkMonitor
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class FakeNetworkMonitor(initial: Boolean = true) : NetworkMonitor {
    private val onlineState = MutableStateFlow(initial)
    override val online: StateFlow<Boolean> = onlineState

    fun set(value: Boolean) {
        onlineState.value = value
    }
}
