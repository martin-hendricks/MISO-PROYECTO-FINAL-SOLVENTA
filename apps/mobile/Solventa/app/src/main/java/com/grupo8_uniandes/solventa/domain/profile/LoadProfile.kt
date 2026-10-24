package com.grupo8_uniandes.solventa.domain.profile

import com.grupo8_uniandes.solventa.domain.consent.ConsentRepository
import com.grupo8_uniandes.solventa.domain.region.RegionRepository
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository

class LoadProfile(
    private val registration: RegistrationRepository,
    private val region: RegionRepository,
    private val permissions: DevicePermissionReader,
    private val consent: ConsentRepository,
    private val session: SessionRepository,
    private val originationActive: Boolean = false,
) {
    operator fun invoke(): ProfileHub {
        val stored = registration.read()
        val reported = permissions.read()
        return ProfileHub(
            identity = stored?.let {
                profileIdentity(it.givenName, it.surnames, it.documentType, it.documentNumber)
            },
            region = region.read().appliedRegion,
            permissions = PermissionKind.entries.map { kind ->
                reported.firstOrNull { it.kind == kind } ?: PermissionRow(kind, published = false)
            },
            consent = consent.read().state,
            originationActive = originationActive,
            sessionOpen = session.isOpen(),
        )
    }
}
