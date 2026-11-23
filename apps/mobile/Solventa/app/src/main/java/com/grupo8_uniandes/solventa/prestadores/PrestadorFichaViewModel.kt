package com.grupo8_uniandes.solventa.prestadores

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.bff.assistance.FindProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider

class PrestadorFichaViewModel(
    prestadorId: String,
    find: FindProviders,
) : ViewModel() {
    val provider: Provider? = find.cached(prestadorId)

    fun directionsUri(): String {
        val row = provider ?: return ""
        return directionsUri(row.lat, row.lng)
    }

    companion object {
        fun directionsUri(lat: Double, lng: Double): String =
            "https://www.google.com/maps/dir/?api=1&destination=$lat,$lng"
    }
}
