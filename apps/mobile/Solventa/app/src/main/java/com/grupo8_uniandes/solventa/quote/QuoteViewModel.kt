package com.grupo8_uniandes.solventa.quote

import androidx.lifecycle.ViewModel
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteAnswers
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteAttempt
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteInput
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteLine
import com.grupo8_uniandes.solventa.domain.bff.offer.RequestFirmOffer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

data class QuoteUiState(
    val line: QuoteLine = QuoteLine.Device,
    val menuOpen: Boolean = false,
    val value: String = "",
    val brand: String = "",
    val olderThan12Months: Boolean? = null,
    val sumInsured: String = "",
    val ageYears: String = "",
    val event: String = "",
    val reference: String = "",
    val threshold: String = "",
    val creditValue: String = "",
    val creditTerm: String = "",
    val installment: String = "",
    val term: String = "",
    val destination: String = "",
    val duration: String = "",
    val gap: QuoteInput? = null,
    val pending: Boolean = false,
    val failed: Boolean = false,
    val readyId: String? = null,
    val contextId: String = "",
)

class QuoteViewModel(
    private val request: RequestFirmOffer,
    contextId: String = "",
) : ViewModel() {
    private val _state = MutableStateFlow(QuoteUiState(contextId = contextId))
    val state: StateFlow<QuoteUiState> = _state.asStateFlow()

    fun onMenu(open: Boolean) {
        _state.update { it.copy(menuOpen = open) }
    }

    fun onLine(line: QuoteLine) {
        val kept = _state.value.contextId
        _state.value = QuoteUiState(line = line, contextId = kept)
    }

    fun onValue(value: String) = onText(QuoteInput.Value, value)

    fun onBrand(brand: String) = onText(QuoteInput.Brand, brand)

    fun onText(input: QuoteInput, text: String) {
        _state.update { state ->
            val updated = when (input) {
                QuoteInput.Value -> state.copy(value = text)
                QuoteInput.Brand -> state.copy(brand = text)
                QuoteInput.SumInsured -> state.copy(sumInsured = text)
                QuoteInput.AgeYears -> state.copy(ageYears = text)
                QuoteInput.Event -> state.copy(event = text)
                QuoteInput.Reference -> state.copy(reference = text)
                QuoteInput.Threshold -> state.copy(threshold = text)
                QuoteInput.CreditValue -> state.copy(creditValue = text)
                QuoteInput.CreditTerm -> state.copy(creditTerm = text)
                QuoteInput.Installment -> state.copy(installment = text)
                QuoteInput.Term -> state.copy(term = text)
                QuoteInput.Destination -> state.copy(destination = text)
                QuoteInput.Duration -> state.copy(duration = text)
                QuoteInput.Age -> state
            }
            updated.copy(gap = null, failed = false)
        }
    }

    fun onAge(olderThan12Months: Boolean) {
        _state.update { it.copy(olderThan12Months = olderThan12Months, gap = null, failed = false) }
    }

    fun cotizar() {
        val current = _state.value
        val answers = QuoteAnswers(
            value = current.value,
            brand = current.brand,
            olderThan12Months = current.olderThan12Months,
            sumInsured = current.sumInsured,
            ageYears = current.ageYears,
            event = current.event,
            reference = current.reference,
            threshold = current.threshold,
            creditValue = current.creditValue,
            creditTerm = current.creditTerm,
            installment = current.installment,
            term = current.term,
            destination = current.destination,
            duration = current.duration,
        )
        when (val attempt = request.submit(current.line, answers)) {
            is QuoteAttempt.Gap -> _state.update {
                it.copy(gap = attempt.field, pending = false, failed = false, readyId = null)
            }
            is QuoteAttempt.Answer -> when (val answer = attempt.answer) {
                StandInAnswer.Pending -> _state.update {
                    it.copy(pending = true, failed = false, gap = null, readyId = null)
                }
                StandInAnswer.Failed -> _state.update {
                    it.copy(pending = false, failed = true, gap = null, readyId = null)
                }
                is StandInAnswer.Ready -> _state.update {
                    it.copy(pending = false, failed = false, gap = null, readyId = answer.value.cotizacionId)
                }
            }
        }
    }

    fun consumeReady() {
        _state.update { it.copy(readyId = null) }
    }

    fun cancel() {
        val kept = _state.value.contextId
        _state.value = QuoteUiState(contextId = kept)
    }
}
