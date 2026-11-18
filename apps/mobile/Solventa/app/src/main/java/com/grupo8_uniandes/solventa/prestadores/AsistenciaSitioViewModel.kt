package com.grupo8_uniandes.solventa.prestadores

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.claim.AssistanceForm
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenAssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.claim.PoliciesInForce
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class AsistenciaSitioViewModel(
    private val prestadorId: String,
    private val assistance: AssistanceRepository,
    private val locator: DeviceLocator,
    private val policiesInForce: PoliciesInForce,
) : ViewModel() {
    private val _form = MutableStateFlow(
        OpenAssistanceRequest().open(locationAllowed = true)?.copy(policyValue = "") ?: AssistanceForm(
            registration = "",
            policyValue = "",
            dateValue = "",
            descriptionValue = "",
            placeValue = "",
        ),
    )
    val form: StateFlow<AssistanceForm> = _form.asStateFlow()
    private val _policies = MutableStateFlow<List<PolicyEntry>>(emptyList())
    val policies: StateFlow<List<PolicyEntry>> = _policies.asStateFlow()
    private val _policiesLoaded = MutableStateFlow(false)
    val policiesLoaded: StateFlow<Boolean> = _policiesLoaded.asStateFlow()

    init {
        viewModelScope.launch {
            val options = policiesInForce()
            _policies.value = options
            _policiesLoaded.value = true
            val selected = when {
                options.size == 1 -> options.single()
                else -> null
            }
            if (selected != null) onPolicy(selected.numero)
        }
    }

    fun onPolicy(numero: String) {
        val entry = _policies.value.firstOrNull { it.numero == numero }
        val label = if (entry == null) numero else "${entry.numero} · ${entry.ramo}"
        edit { copy(policyValue = label) }
    }

    fun onDate(value: String) = edit { copy(dateValue = value) }

    fun onDescription(value: String) = edit { copy(descriptionValue = value) }

    fun onPlace(value: String) = edit { copy(placeValue = value) }

    fun submit() {
        val current = _form.value
        viewModelScope.launch {
            val geo = runCatching { locator.current() }.getOrNull()
            assistance.request(
                AssistanceRequest(
                    prestadorId = prestadorId,
                    lat = geo?.lat ?: 0.0,
                    lng = geo?.lng ?: 0.0,
                    poliza = current.policyValue.substringBefore(" · ").trim(),
                ),
            )
        }
    }

    private inline fun edit(block: AssistanceForm.() -> AssistanceForm) {
        _form.value = _form.value.block()
    }
}
