package com.grupo8_uniandes.solventa.login

import com.grupo8_uniandes.solventa.domain.login.DeviceUnlock
import com.grupo8_uniandes.solventa.domain.login.SignIn
import com.grupo8_uniandes.solventa.domain.login.SignInResult
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.ui.login.LoginEffect
import com.grupo8_uniandes.solventa.ui.login.LoginFailure
import com.grupo8_uniandes.solventa.ui.login.LoginViewModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
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
        assertEquals("camila@correo.com", viewModel.state.value.email)
        assertEquals("secret", viewModel.state.value.password)
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
    fun givenAcceptedDeviceUnlock_whenHandled_thenOpenHomeWithoutEditingFields() {
        val signIn = ScriptedSignIn(mutableListOf())
        val viewModel = LoginViewModel(signIn)
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.onDeviceUnlock(DeviceUnlock.Accepted)

        assertEquals(LoginEffect.OpenHome, viewModel.state.value.effect)
        assertEquals(LoginFailure.None, viewModel.state.value.failure)
        assertEquals("camila@correo.com", viewModel.state.value.email)
        assertEquals("secret", viewModel.state.value.password)
        assertEquals(0, signIn.calls)
    }

    @Test
    fun givenDismissedOrUnavailableDeviceUnlock_whenHandled_thenKeepCurrentState() {
        val signIn = ScriptedSignIn(mutableListOf())
        val viewModel = LoginViewModel(signIn)
        viewModel.onEmail("camila@correo.com")
        viewModel.onPassword("secret")

        viewModel.onDeviceUnlock(DeviceUnlock.Dismissed)
        assertNull(viewModel.state.value.effect)
        assertEquals(LoginFailure.None, viewModel.state.value.failure)
        assertEquals("camila@correo.com", viewModel.state.value.email)
        assertEquals("secret", viewModel.state.value.password)

        viewModel.onDeviceUnlock(DeviceUnlock.Unavailable)
        assertNull(viewModel.state.value.effect)
        assertEquals(LoginFailure.None, viewModel.state.value.failure)
        assertEquals("camila@correo.com", viewModel.state.value.email)
        assertEquals("secret", viewModel.state.value.password)
        assertEquals(0, signIn.calls)
    }
}

private class ScriptedSignIn(
    private val results: MutableList<SignInResult>,
) : SignIn(ThrowingRegistrationRepository()) {
    var calls: Int = 0

    override fun submit(email: String, password: String): SignInResult {
        calls += 1
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
