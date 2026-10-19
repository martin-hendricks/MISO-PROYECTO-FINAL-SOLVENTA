package com.grupo8_uniandes.solventa.domain.startup

open class ResolvePostSplashStep {
    open operator fun invoke(session: StartupSession): PostSplashStep = when (session) {
        StartupSession.FirstUse -> PostSplashStep.LanguageAndRegion
        StartupSession.ExistingAccount -> PostSplashStep.Login
    }
}
