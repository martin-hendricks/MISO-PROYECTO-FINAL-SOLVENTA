package com.grupo8_uniandes.solventa.domain.bff.claim

interface DeviceLocator {
    suspend fun current(): GeoPoint?
}
