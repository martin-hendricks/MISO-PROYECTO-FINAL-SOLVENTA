package com.grupo8_uniandes.solventa.domain.network

import kotlinx.coroutines.flow.StateFlow

interface NetworkMonitor {
    val online: StateFlow<Boolean>
}
