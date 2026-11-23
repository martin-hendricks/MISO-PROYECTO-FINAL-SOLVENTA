package com.grupo8_uniandes.solventa.data.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import com.grupo8_uniandes.solventa.domain.network.NetworkMonitor
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class ConnectivityNetworkMonitor(context: Context) : NetworkMonitor {
    private val manager = context.applicationContext.getSystemService(ConnectivityManager::class.java)
    private val onlineState = MutableStateFlow(validated())
    override val online: StateFlow<Boolean> = onlineState.asStateFlow()

    init {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) = publish()
            override fun onLost(network: Network) {
                onlineState.value = false
            }
            override fun onCapabilitiesChanged(network: Network, capabilities: NetworkCapabilities) {
                onlineState.value = capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
            }
        }
        val connectivity = manager
        if (connectivity != null) {
            runCatching { connectivity.registerDefaultNetworkCallback(callback) }
        }
    }

    private fun publish() {
        onlineState.value = validated()
    }

    private fun validated(): Boolean {
        val capabilities = manager?.getNetworkCapabilities(manager.activeNetwork) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }
}
