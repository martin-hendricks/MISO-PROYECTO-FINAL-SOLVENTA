package com.grupo8_uniandes.solventa.home

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class OfferSummary(val label: String)

data class PolicySummary(val policyId: String)

data class HomeSummary(
    val offer: OfferSummary? = null,
    val policy: PolicySummary? = null,
)

data class ProfileEntry(val id: String, val label: String)

data class HomeUiState(
    val summary: HomeSummary = HomeSummary(),
    val quoteActionLabel: String = "Nueva cotización",
    val showEnrichedHome: Boolean = false,
)

class HomeViewModel @JvmOverloads constructor(
    initial: HomeSummary = HomeSummary(),
) : ViewModel() {
    private val _state = MutableStateFlow(HomeUiState(summary = initial))
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

    val profileEntries: List<ProfileEntry> = listOf(
        ProfileEntry(id = "IdiomaRegion", label = "Idioma y región"),
    )
}
