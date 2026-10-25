package com.grupo8_uniandes.solventa.login

import com.grupo8_uniandes.solventa.domain.login.DeviceUnlock
import com.grupo8_uniandes.solventa.domain.login.SignIn
import com.grupo8_uniandes.solventa.domain.login.SignInResult
import com.grupo8_uniandes.solventa.domain.registration.BiometricLogin
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.ui.login.LoginEffect
import com.grupo8_uniandes.solventa.ui.login.LoginFailure
import com.grupo8_uniandes.solventa.ui.login.LoginViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class LoginViewModelTest {
    @Test
    fun givenNewScreen_whenOpened_thenFieldsAreEmpty() {
        val signIn = ScriptedSignIn(mutableListOf())
        val viewModel = LoginViewModel(signIn)

        assertEquals("", viewModel.state.value.email)
        assertEquals("", viewModel.state.value.password)
        assertEquals(LoginFailure.None, viewModel.state.value.failure)
        assertNull(viewModel.state.value.effect)
        assertEquals(0, signIn.calls)
    }

    @Test
    fun givenSignedIn_whenIngresarAgain_thenHomeOpensOnce() {
        val signIn = ScriptedSignIn(mutableListOf(SignInResult.SignedIn, SignInResult.SignedIn))
        val viewModel = LoginViewModel(signIn)
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.ingresar()
        viewModel.onEmail("other@correo.com")
        viewModel.onPassword("nope")
        viewModel.ingresar()

        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
        assertEquals(1, signIn.calls)
        assertEquals("", viewModel.state.value.email)
        assertEquals("", viewModel.state.value.password)
    }

    @Test
    fun givenAttemptInProgress_whenIngresarAgain_thenUseCaseRunsOnce() {
        lateinit var viewModel: LoginViewModel
        val signIn = ReenteringSignIn {
            viewModel.onEmail("other@correo.com")
            viewModel.onPassword("nope")
            viewModel.ingresar()
        }
        viewModel = LoginViewModel(signIn)
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.ingresar()

        assertEquals(1, signIn.calls)
        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
    }

    @Test
    fun givenRejected_whenShown_thenCredentialFailureKeepsThePassword() {
        val signIn = ScriptedSignIn(
            mutableListOf(SignInResult.Rejected, SignInResult.SignedIn),
        )
        val viewModel = LoginViewModel(signIn)
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("wrong")

        viewModel.ingresar()

        assertEquals("camila@correo.com", viewModel.state.value.email)
        assertEquals("wrong", viewModel.state.value.password)
        assertEquals(LoginFailure.Rejected, viewModel.state.value.failure)
        assertNull(viewModel.state.value.effect)

        viewModel.onPassword("secret")
        viewModel.ingresar()

        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
        assertEquals(2, signIn.calls)
    }

    @Test
    fun givenBlank_whenIngresar_thenNoFailure() {
        val signIn = ScriptedSignIn(mutableListOf(SignInResult.Incomplete))
        val viewModel = LoginViewModel(signIn)
        viewModel.onEmail("   ")
        viewModel.onPassword("secret")

        viewModel.ingresar()

        assertEquals(LoginFailure.None, viewModel.state.value.failure)
        assertEquals("secret", viewModel.state.value.password)
        assertNull(viewModel.state.value.effect)
    }

    @Test
    fun givenUnavailable_whenIngresar_thenConnectionFailureKeepsTheDraft() {
        val signIn = ScriptedSignIn(
            mutableListOf(SignInResult.Unavailable, SignInResult.SignedIn),
        )
        val viewModel = LoginViewModel(signIn)
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.ingresar()

        assertEquals(LoginFailure.Unavailable, viewModel.state.value.failure)
        assertEquals("camila@correo.com", viewModel.state.value.email)
        assertEquals("secret", viewModel.state.value.password)
        assertNull(viewModel.state.value.effect)

        viewModel.ingresar()

        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
    }

    @Test
    fun givenStoredLogin_whenBiometricAccepted_thenSignInUsesThatPair() {
        val signIn = ScriptedSignIn(mutableListOf(SignInResult.SignedIn))
        var remembered: BiometricLogin? = null
        val viewModel = LoginViewModel(
            signIn = signIn,
            storedBiometricLogin = { BiometricLogin("camila@correo.com", "secret") },
            rememberBiometricLogin = { email, password ->
                remembered = BiometricLogin(email, password)
            },
        )
        viewModel.onEmail("typed@correo.com")
        viewModel.onPassword("typed")

        viewModel.onDeviceUnlock(DeviceUnlock.Accepted)

        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
        assertFalse(viewModel.state.value.biometricFallback)
        assertEquals(LoginFailure.None, viewModel.state.value.failure)
        assertEquals("", viewModel.state.value.email)
        assertEquals("", viewModel.state.value.password)
        assertEquals(1, signIn.calls)
        assertEquals("camila@correo.com", signIn.email)
        assertEquals("secret", signIn.password)
        assertEquals(BiometricLogin("camila@correo.com", "secret"), remembered)
    }

    @Test
    fun givenNoStoredLogin_whenBiometricAccepted_thenFallbackStaysClosed() {
        val signIn = ScriptedSignIn(mutableListOf())
        val viewModel = LoginViewModel(signIn)

        viewModel.onDeviceUnlock(DeviceUnlock.Accepted)

        assertNull(viewModel.state.value.effect)
        assertTrue(viewModel.state.value.biometricFallback)
        assertEquals(0, signIn.calls)
    }

    @Test
    fun givenStoredLoginRejected_whenBiometricAccepted_thenFallbackShowsTheError() {
        val signIn = ScriptedSignIn(mutableListOf(SignInResult.Rejected))
        val viewModel = LoginViewModel(
            signIn = signIn,
            storedBiometricLogin = { BiometricLogin("camila@correo.com", "wrong") },
        )

        viewModel.onDeviceUnlock(DeviceUnlock.Accepted)

        assertNull(viewModel.state.value.effect)
        assertTrue(viewModel.state.value.biometricFallback)
        assertEquals(LoginFailure.Rejected, viewModel.state.value.failure)
        assertEquals(1, signIn.calls)
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenStoredLogin_whenRemoteSessionOpens_thenHomeUsesThatPair() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        try {
            val signIn = ScriptedSignIn(mutableListOf(SignInResult.SignedIn))
            var opened: BiometricLogin? = null
            val viewModel = LoginViewModel(
                signIn = signIn,
                openRemoteSession = { email, password ->
                    opened = BiometricLogin(email, password)
                    true
                },
                storedBiometricLogin = { BiometricLogin("camila@correo.com", "secret") },
            )

            viewModel.onDeviceUnlock(DeviceUnlock.Accepted)

            assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
            assertEquals(BiometricLogin("camila@correo.com", "secret"), opened)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun givenPasswordSignIn_whenAccepted_thenPairIsStoredForBiometria() {
        val signIn = ScriptedSignIn(mutableListOf(SignInResult.SignedIn))
        var remembered: BiometricLogin? = null
        val viewModel = LoginViewModel(
            signIn = signIn,
            rememberBiometricLogin = { email, password ->
                remembered = BiometricLogin(email, password)
            },
        )
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.ingresar()

        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
        assertEquals("", viewModel.state.value.email)
        assertEquals("", viewModel.state.value.password)
        assertEquals(BiometricLogin("camila@correo.com", "secret"), remembered)
    }

    @Test
    fun givenDismissedDeviceUnlock_whenHandled_thenFallbackCanSignIn() {
        val signIn = ScriptedSignIn(mutableListOf(SignInResult.SignedIn))
        val viewModel = LoginViewModel(signIn)
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.onDeviceUnlock(DeviceUnlock.Dismissed)
        assertNull(viewModel.state.value.effect)
        assertTrue(viewModel.state.value.biometricFallback)
        assertEquals(LoginFailure.None, viewModel.state.value.failure)
        assertEquals("camila@correo.com", viewModel.state.value.email)
        assertEquals("secret", viewModel.state.value.password)
        assertEquals(0, signIn.calls)

        viewModel.ingresar()
        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
        assertEquals(1, signIn.calls)
    }

    @Test
    fun givenUnavailableDeviceUnlock_whenHandled_thenFallbackCanSignIn() {
        val signIn = ScriptedSignIn(mutableListOf(SignInResult.SignedIn))
        val viewModel = LoginViewModel(signIn)
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.onDeviceUnlock(DeviceUnlock.Unavailable)
        assertNull(viewModel.state.value.effect)
        assertTrue(viewModel.state.value.biometricFallback)
        assertEquals(LoginFailure.None, viewModel.state.value.failure)
        assertEquals("camila@correo.com", viewModel.state.value.email)
        assertEquals("secret", viewModel.state.value.password)
        assertEquals(0, signIn.calls)

        viewModel.ingresar()
        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
        assertEquals(1, signIn.calls)
    }

    @Test
    fun givenDismissedDeviceUnlock_whenRejectedOrBlank_thenHomeStaysClosed() {
        val signIn = ScriptedSignIn(
            mutableListOf(SignInResult.Rejected, SignInResult.Incomplete),
        )
        val viewModel = LoginViewModel(signIn)
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("wrong")

        viewModel.onDeviceUnlock(DeviceUnlock.Dismissed)
        viewModel.ingresar()

        assertEquals(LoginFailure.Rejected, viewModel.state.value.failure)
        assertNull(viewModel.state.value.effect)
        assertEquals(1, signIn.calls)

        viewModel.onEmail("   ")
        viewModel.onPassword("secret")
        viewModel.ingresar()

        assertEquals(LoginFailure.None, viewModel.state.value.failure)
        assertNull(viewModel.state.value.effect)
        assertEquals("   ", viewModel.state.value.email)
        assertEquals("secret", viewModel.state.value.password)
        assertEquals(2, signIn.calls)
    }

    @Test
    fun givenPasswordWithoutBiometric_whenAccepted_thenUnlockIsStoredAndHomeOpens() {
        var enabled = false
        val viewModel = LoginViewModel(
            signIn = ScriptedSignIn(mutableListOf(SignInResult.SignedIn)),
            biometricEnabled = { enabled },
            enableBiometric = { enabled = true },
        )
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.ingresar()

        assertEquals(LoginEffect.ConfirmBiometric, viewModel.state.value.effect)
        viewModel.acceptBiometric()
        assertTrue(enabled)
        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
    }

    @Test
    fun givenPasswordWithoutBiometric_whenDeclined_thenHomeOpensWithoutUnlock() {
        var enabled = false
        val viewModel = LoginViewModel(
            signIn = ScriptedSignIn(mutableListOf(SignInResult.SignedIn)),
            biometricEnabled = { enabled },
            enableBiometric = { enabled = true },
        )
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.ingresar()
        viewModel.declineBiometric()

        assertFalse(enabled)
        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
        viewModel.consumeEffect()
        assertNull(viewModel.state.value.effect)
    }
}

private class ScriptedSignIn(
    private val results: MutableList<SignInResult>,
) : SignIn(ThrowingRegistrationRepository()) {
    var calls: Int = 0
    var email: String = ""
    var password: String = ""

    override fun submit(email: String, password: String): SignInResult {
        calls += 1
        this.email = email
        this.password = password
        return results.removeAt(0)
    }
}

private class ReenteringSignIn(
    private val again: () -> Unit,
) : SignIn(ThrowingRegistrationRepository()) {
    var calls: Int = 0

    override fun submit(email: String, password: String): SignInResult {
        calls += 1
        if (calls == 1) again()
        return SignInResult.SignedIn
    }
}

private class ThrowingRegistrationRepository : RegistrationRepository {
    override fun read(): Registration? = error("production repository")

    override fun save(registration: Registration) = error("production repository")
}
