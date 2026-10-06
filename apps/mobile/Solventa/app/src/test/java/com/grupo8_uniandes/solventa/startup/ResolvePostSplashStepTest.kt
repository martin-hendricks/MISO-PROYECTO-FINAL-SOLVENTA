package com.grupo8_uniandes.solventa.startup

import com.grupo8_uniandes.solventa.domain.startup.PostSplashStep
import com.grupo8_uniandes.solventa.domain.startup.ResolvePostSplashStep
import com.grupo8_uniandes.solventa.domain.startup.StartupSession
import org.junit.Assert.assertEquals
import org.junit.Test

class ResolvePostSplashStepTest {
    private val resolve = ResolvePostSplashStep()

    @Test
    fun givenFirstUse_whenStartupFinishes_thenLanguageAndRegion() {
        assertEquals(PostSplashStep.LanguageAndRegion, resolve(StartupSession.FirstUse))
    }

    @Test
    fun givenExistingAccount_whenStartupFinishes_thenLogin() {
        assertEquals(PostSplashStep.Login, resolve(StartupSession.ExistingAccount))
    }
}
