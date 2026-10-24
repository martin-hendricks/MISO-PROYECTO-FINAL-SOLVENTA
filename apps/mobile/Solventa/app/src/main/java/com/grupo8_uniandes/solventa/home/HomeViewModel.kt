package com.grupo8_uniandes.solventa.home

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.domain.home.LoadInicio
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class HomeUiState(
    val panel: HomePanel = HomePanel(),
)

class HomeViewModel(
    loadInicio: LoadInicio,
) : ViewModel() {
    private val _state = MutableStateFlow(HomeUiState(panel = loadInicio.panel()))
    val state: StateFlow<HomeUiState> = _state.asStateFlow()
}
