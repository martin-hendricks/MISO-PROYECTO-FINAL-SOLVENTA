package com.grupo8_uniandes.solventa.ui.region

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.region.ConfirmFirstLaunch
import com.grupo8_uniandes.solventa.domain.region.ConfirmFromProfile
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.RegionChoice
import com.grupo8_uniandes.solventa.domain.region.RegionRepository
import com.grupo8_uniandes.solventa.domain.region.StageRegion
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

enum class RegionSurface {
    FirstLaunch,
    Profile,
}

sealed interface RegionEffect {
    data object ContinueToHome : RegionEffect

    data object CloseSheet : RegionEffect
}

data class IdiomaRegionUiState(
    val choice: RegionChoice,
    val effect: RegionEffect? = null,
)

class IdiomaRegionViewModel(
    private val repository: RegionRepository,
    private val surface: RegionSurface,
    private val stageRegion: StageRegion = StageRegion(repository),
    private val confirmFirstLaunch: ConfirmFirstLaunch = ConfirmFirstLaunch(repository),
    private val confirmFromProfile: ConfirmFromProfile = ConfirmFromProfile(repository),
) : ViewModel() {
    private val _state = MutableStateFlow(initialState())
    val state: StateFlow<IdiomaRegionUiState> = _state.asStateFlow()

    fun select(region: Region) {
        _state.value = IdiomaRegionUiState(stageRegion(region))
    }

    fun confirm() {
        val choice = when (surface) {
            RegionSurface.FirstLaunch -> confirmFirstLaunch()
            RegionSurface.Profile -> confirmFromProfile()
        }
        val effect = when (surface) {
            RegionSurface.FirstLaunch -> RegionEffect.ContinueToHome
            RegionSurface.Profile -> RegionEffect.CloseSheet
        }
        _state.value = IdiomaRegionUiState(choice, effect)
    }

    fun dismiss() {
        if (surface != RegionSurface.Profile) return
        _state.value = _state.value.copy(effect = RegionEffect.CloseSheet)
    }

    fun syncToApplied() {
        val applied = repository.read().appliedRegion
        _state.value = IdiomaRegionUiState(stageRegion(applied))
    }

    private fun initialState(): IdiomaRegionUiState {
        val choice = repository.read()
        return if (surface == RegionSurface.Profile) {
            IdiomaRegionUiState(stageRegion(choice.appliedRegion))
        } else {
            IdiomaRegionUiState(choice)
        }
    }
}
