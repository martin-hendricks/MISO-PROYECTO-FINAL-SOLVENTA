package com.grupo8_uniandes.solventa.ui.shell

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.profile.LoadProfile
import com.grupo8_uniandes.solventa.domain.profile.ProfileHub
import com.grupo8_uniandes.solventa.domain.profile.SignOut
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.runBlocking

class ProfileViewModel(
    private val load: LoadProfile,
    private val signOut: SignOut,
) : ViewModel() {
    private val _state = MutableStateFlow(load())
    val state: StateFlow<ProfileHub> = _state.asStateFlow()

    private val _signedOut = MutableStateFlow(false)
    val signedOut: StateFlow<Boolean> = _signedOut.asStateFlow()

    fun confirmSignOut() {
        if (_signedOut.value) return
        runBlocking { signOut.complete() }
        _signedOut.value = true
    }

    fun consumeSignOut() {
        _signedOut.value = false
    }
}
