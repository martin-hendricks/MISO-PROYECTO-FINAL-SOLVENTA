package com.grupo8_uniandes.solventa.ui.shell

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.startup.PostSplashStep
import com.grupo8_uniandes.solventa.domain.startup.ResolvePostSplashStep
import com.grupo8_uniandes.solventa.domain.startup.StartupSession
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

sealed interface SplashUiState {
    data object Showing : SplashUiState

    data class Finished(val step: PostSplashStep) : SplashUiState
}

class SplashViewModel(
    private val session: StartupSession = StartupSession.FirstUse,
    private val resolve: ResolvePostSplashStep = ResolvePostSplashStep(),
    private val holdMillis: Long = SplashHoldMillis,
    private val awaitHold: suspend (Long) -> Unit = { delay(it) },
) : ViewModel() {
    private val _state = MutableStateFlow<SplashUiState>(SplashUiState.Showing)
    val state: StateFlow<SplashUiState> = _state.asStateFlow()

    suspend fun start() {
        if (_state.value is SplashUiState.Finished) return
        val step = resolve(session)
        awaitHold(holdMillis)
        _state.value = SplashUiState.Finished(step)
    }
}
