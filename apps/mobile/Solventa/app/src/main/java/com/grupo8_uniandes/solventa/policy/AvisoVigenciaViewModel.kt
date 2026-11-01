package com.grupo8_uniandes.solventa.policy

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.grupo8_uniandes.solventa.domain.bff.notice.OpenValidityNotice
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityReading
import com.grupo8_uniandes.solventa.domain.bff.push.PushNotice
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class AvisoVigenciaViewModel(
    private val notices: OpenValidityNotice,
) : ViewModel() {
    private val _reading = MutableStateFlow<ValidityReading?>(null)
    val reading: StateFlow<ValidityReading?> = _reading.asStateFlow()

    fun loadExpiry() {
        viewModelScope.launch { _reading.value = notices.openExpiry() }
    }

    fun loadRenewal() {
        viewModelScope.launch { _reading.value = notices.openRenewal() }
    }

    fun openPush(push: PushNotice) {
        viewModelScope.launch { _reading.value = notices.open(push) }
    }

    fun requestExpiry(poliza: String, onResult: (ValidityReading?) -> Unit) {
        viewModelScope.launch {
            val reading = notices.openExpiry()
            onResult(reading?.takeIf { it.poliza == poliza })
        }
    }
}
