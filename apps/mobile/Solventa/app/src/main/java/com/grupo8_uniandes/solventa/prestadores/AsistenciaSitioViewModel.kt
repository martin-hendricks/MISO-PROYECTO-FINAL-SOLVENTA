package com.grupo8_uniandes.solventa.prestadores

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import kotlinx.coroutines.launch

class AsistenciaSitioViewModel(
    private val prestadorId: String,
    private val assistance: AssistanceRepository,
    private val locator: DeviceLocator,
) : ViewModel() {
    fun submit() {
        viewModelScope.launch {
            val geo = locator.current() ?: return@launch
            assistance.request(
                AssistanceRequest(
                    prestadorId = prestadorId,
                    lat = geo.lat,
                    lng = geo.lng,
                    poliza = "",
                ),
            )
        }
    }
}
