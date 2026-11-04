package com.grupo8_uniandes.solventa.policy

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.policy.RenewalSave
import com.grupo8_uniandes.solventa.domain.bff.policy.SaveRenewalPreference
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class RenewalChoiceUi(
    val checked: Boolean = false,
    val missing: Boolean = false,
)

class RenewalChoiceViewModel(
    private val numero: String,
    private val save: SaveRenewalPreference,
) : ViewModel() {
    private val _state = MutableStateFlow(RenewalChoiceUi())
    val state: StateFlow<RenewalChoiceUi> = _state.asStateFlow()

    fun onChecked(enabled: Boolean) {
        val previous = _state.value.checked
        _state.value = RenewalChoiceUi(checked = enabled, missing = false)
        viewModelScope.launch {
            _state.value = when (val result = save(numero, enabled)) {
                is RenewalSave.Saved -> RenewalChoiceUi(checked = result.enabled, missing = false)
                RenewalSave.Missing -> RenewalChoiceUi(checked = previous, missing = true)
                RenewalSave.Failed -> RenewalChoiceUi(checked = previous, missing = false)
            }
        }
    }
}
