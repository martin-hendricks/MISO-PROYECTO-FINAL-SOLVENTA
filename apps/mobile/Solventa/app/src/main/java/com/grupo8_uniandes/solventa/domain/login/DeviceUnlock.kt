package com.grupo8_uniandes.solventa.domain.login

enum class DeviceUnlock {
    Accepted,
    Dismissed,
    Unavailable,
}

class OpenHomeFromDeviceUnlock {
    operator fun invoke(result: DeviceUnlock): Boolean = result == DeviceUnlock.Accepted
}
