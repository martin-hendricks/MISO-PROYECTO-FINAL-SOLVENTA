package com.grupo8_uniandes.solventa.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.domain.home.LoadInicio
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.coroutines.coroutineContext

data class HomeUiState(
    val panel: HomePanel = HomePanel(),
    val failed: Boolean = false,
)

class HomeViewModel(
    private val loadInicio: LoadInicio,
    private val reloadDispatcher: CoroutineDispatcher = Dispatchers.IO,
) : ViewModel() {
    private val _state = MutableStateFlow(read())
    val state: StateFlow<HomeUiState> = _state.asStateFlow()
    private var loadJob: Job? = null

    fun refresh() {
        if (loadJob?.isActive == true) return
        loadJob = viewModelScope.launch {
            val panel = withContext(reloadDispatcher) { loadInicio.panel() }
            coroutineContext.ensureActive()
            _state.value = if (panel == null) {
                _state.value.copy(failed = true)
            } else {
                HomeUiState(panel = panel, failed = false)
            }
        }
    }

    private fun read(): HomeUiState {
        val panel = loadInicio.panel()
        return if (panel == null) HomeUiState(failed = true) else HomeUiState(panel = panel)
    }
}
