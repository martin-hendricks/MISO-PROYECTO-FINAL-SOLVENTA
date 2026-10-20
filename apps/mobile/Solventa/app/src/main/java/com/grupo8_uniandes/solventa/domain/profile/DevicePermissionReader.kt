package com.grupo8_uniandes.solventa.domain.profile

fun interface DevicePermissionReader {
    fun read(): List<PermissionRow>
}
