package com.grupo8_uniandes.solventa.startup

import com.grupo8_uniandes.solventa.domain.startup.PostSplashStep
import com.grupo8_uniandes.solventa.domain.startup.ResolvePostSplashStep
import com.grupo8_uniandes.solventa.domain.startup.StartupSession
import com.grupo8_uniandes.solventa.ui.shell.SplashUiState
import com.grupo8_uniandes.solventa.ui.shell.SplashViewModel
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test

class SplashViewModelTest {
    @Test
    fun givenHold_whenAdvanced_thenFinishedWithFakedStep() = runBlocking {
        val fake = object : ResolvePostSplashStep() {
            override fun invoke(session: StartupSession): PostSplashStep = PostSplashStep.Login
        }
        var waited = -1L
        val viewModel = SplashViewModel(
            session = StartupSession.FirstUse,
            resolve = fake,
            holdMillis = 1_500L,
            awaitHold = { millis -> waited = millis },
        )

        assertEquals(SplashUiState.Showing, viewModel.state.value)
        viewModel.start()

        assertEquals(1_500L, waited)
        assertEquals(SplashUiState.Finished(PostSplashStep.Login), viewModel.state.value)
    }

    @Test
    fun givenFinishedSplash_whenStartRunsAgain_thenHoldIsNotRepeated() = runBlocking {
        var waits = 0
        val viewModel = SplashViewModel(
            session = StartupSession.ExistingAccount,
            resolve = ResolvePostSplashStep(),
            holdMillis = 10L,
            awaitHold = { waits += 1 },
        )

        viewModel.start()
        viewModel.start()

        assertEquals(1, waits)
        assertEquals(SplashUiState.Finished(PostSplashStep.Login), viewModel.state.value)
    }
}
