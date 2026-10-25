package com.grupo8_uniandes.solventa.profile

import com.grupo8_uniandes.solventa.domain.consent.ConsentRecord
import com.grupo8_uniandes.solventa.domain.consent.ConsentRepository
import com.grupo8_uniandes.solventa.domain.consent.ConsentSnapshot
import com.grupo8_uniandes.solventa.domain.profile.LoadProfile
import com.grupo8_uniandes.solventa.domain.profile.PermissionRow
import com.grupo8_uniandes.solventa.domain.profile.SessionRepository
import com.grupo8_uniandes.solventa.domain.profile.SignOut
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.RegionChoice
import com.grupo8_uniandes.solventa.domain.region.RegionRepository
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.ui.shell.ProfileViewModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ProfileViewModelTest {
    @Test
    fun givenAHub_whenLoaded_thenThereIsNoEditAction() {
        val viewModel = viewModel()
        assertEquals("Camila Restrepo", viewModel.state.value.identity?.name)
        assertFalse(viewModel.signedOut.value)
    }

    @Test
    fun givenSignOutConfirmed_whenCalled_thenSessionClosesOnce() {
        val session = MemorySession()
        val viewModel = viewModel(session)
        viewModel.confirmSignOut()
        viewModel.confirmSignOut()
        assertTrue(viewModel.signedOut.value)
        assertEquals(1, session.closes)
        assertFalse(session.isOpen())
        viewModel.consumeSignOut()
        assertFalse(viewModel.signedOut.value)
    }

    private fun viewModel(session: SessionRepository = MemorySession()) = ProfileViewModel(
        load = LoadProfile(
            registration = object : RegistrationRepository {
                override fun read() = Registration(
                    givenName = "Camila",
                    surnames = "Restrepo",
                    email = "camila@example.com",
                    documentType = "CC",
                    documentNumber = "1",
                    password = "secret",
                    documentPhoto = byteArrayOf(1),
                )
                override fun save(registration: Registration) = Unit
            },
            region = object : RegionRepository {
                override fun read() = RegionChoice(firstLaunchCompleted = true)
                override fun stage(region: Region) = read()
                override fun confirmFirstLaunch() = read()
                override fun confirmFromProfile() = read()
            },
            permissions = { emptyList<PermissionRow>() },
            consent = object : ConsentRepository {
                override fun read() = ConsentSnapshot()
                override fun append(record: ConsentRecord) = Unit
            },
            session = session,
        ),
        signOut = SignOut(session),
    )
}

class MemorySession : SessionRepository {
    var closes: Int = 0
    private var open: Boolean = true

    override fun isOpen(): Boolean = open

    override fun close() {
        closes += 1
        open = false
    }

    override fun open() {
        open = true
    }
}
