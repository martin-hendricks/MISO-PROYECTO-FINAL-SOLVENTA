package com.grupo8_uniandes.solventa.profile

import com.grupo8_uniandes.solventa.domain.consent.ConsentRecord
import com.grupo8_uniandes.solventa.domain.consent.ConsentRepository
import com.grupo8_uniandes.solventa.domain.consent.ConsentSnapshot
import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import com.grupo8_uniandes.solventa.domain.profile.DevicePermissionReader
import com.grupo8_uniandes.solventa.domain.profile.LoadProfile
import com.grupo8_uniandes.solventa.domain.profile.PermissionKind
import com.grupo8_uniandes.solventa.domain.profile.PermissionRow
import com.grupo8_uniandes.solventa.domain.profile.SessionRepository
import com.grupo8_uniandes.solventa.domain.profile.profileIdentity
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.RegionChoice
import com.grupo8_uniandes.solventa.domain.region.RegionRepository
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class LoadProfileTest {
    @Test
    fun givenNamesAndDocument_whenLoaded_thenHeaderJoinsTheStoredParts() {
        val hub = load(
            registration = registration(givenName = "Camila", surnames = "Restrepo"),
        )
        assertEquals("Camila Restrepo", hub.identity?.name)
        assertEquals("CC 1.023.456.789", hub.identity?.document)
        assertTrue(hub.sessionOpen)
    }

    @Test
    fun givenBlankDocumentNumber_whenLoaded_thenDocumentOmitsTheGap() {
        val hub = load(
            registration = Registration(
                givenName = "Camila",
                surnames = "Restrepo",
                email = "camila@example.com",
                documentType = "CC",
                documentNumber = " ",
                password = "secret",
                documentPhoto = byteArrayOf(1),
            ),
        )
        assertEquals("CC", hub.identity?.document)
    }

    @Test
    fun givenBlankSurnames_whenLoaded_thenNameHasNoExtraSpace() {
        val hub = load(registration = registration(givenName = "Camila", surnames = "  "))
        assertEquals("Camila", hub.identity?.name)
    }

    @Test
    fun givenNoRegistration_whenLoaded_thenIdentityIsAbsent() {
        val hub = load(registration = null)
        assertNull(hub.identity)
        assertFalse(hub.identity?.name == "Camila Restrepo")
    }

    @Test
    fun givenPartialPermissions_whenLoaded_thenThreeRowsRemain() {
        val hub = load(
            permissions = listOf(PermissionRow(PermissionKind.Camera, published = false)),
        )
        assertEquals(PermissionKind.entries, hub.permissions.map { it.kind })
        assertTrue(hub.permissions.none { it.published })
    }

    @Test
    fun givenOriginationFalse_whenLoaded_thenFlagStaysFalse() {
        val hub = load(origination = false)
        assertFalse(hub.originationActive)
        assertEquals(ConsentState.Granted, hub.consent)
    }

    @Test
    fun givenEachRegion_whenLoaded_thenThatRegionIsKept() {
        assertEquals(Region.Colombia, load(region = Region.Colombia).region)
        assertEquals(Region.Mexico, load(region = Region.Mexico).region)
        assertEquals(Region.Chile, load(region = Region.Chile).region)
        assertEquals(Region.Peru, load(region = Region.Peru).region)
        assertTrue(profileIdentity("A", "B", "CC", "1").document == "CC 1")
    }

    @Test
    fun givenOriginationTrue_whenLoaded_thenConsentIsUnchanged() {
        val hub = load(origination = true, consent = ConsentState.Revoked)
        assertTrue(hub.originationActive)
        assertEquals(ConsentState.Revoked, hub.consent)
    }

    private fun load(
        registration: Registration? = registration(),
        region: Region = Region.Colombia,
        permissions: List<PermissionRow> = emptyList(),
        consent: ConsentState = ConsentState.Granted,
        origination: Boolean = false,
    ) = LoadProfile(
        registration = object : RegistrationRepository {
            override fun read() = registration
            override fun save(registration: Registration) = Unit
        },
        region = object : RegionRepository {
            override fun read() = RegionChoice(appliedRegion = region, draftRegion = region, firstLaunchCompleted = true)
            override fun stage(region: Region) = read()
            override fun confirmFirstLaunch() = read()
            override fun confirmFromProfile() = read()
        },
        permissions = DevicePermissionReader { permissions },
        consent = object : ConsentRepository {
            override fun read() = ConsentSnapshot(state = consent)
            override fun append(record: ConsentRecord) = Unit
        },
        session = object : SessionRepository {
            override fun isOpen() = true
            override fun close() = Unit
            override fun open() = Unit
        },
        originationActive = origination,
    )()

    private fun registration(
        givenName: String = "Camila",
        surnames: String = "Restrepo",
    ) = Registration(
        givenName = givenName,
        surnames = surnames,
        email = "camila@example.com",
        documentType = "CC",
        documentNumber = "1.023.456.789",
        password = "secret",
        documentPhoto = byteArrayOf(1),
    )
}
