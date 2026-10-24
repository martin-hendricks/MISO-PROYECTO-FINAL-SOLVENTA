package com.grupo8_uniandes.solventa.domain.bff.offer

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

sealed interface QuoteAttempt {
    data class Gap(val field: QuoteInput) : QuoteAttempt

    data class Answer(val answer: StandInAnswer<FirmOffer>) : QuoteAttempt
}

/**
 * Asks the stand-in only after the selected line has its answers.
 * The prepared premium stays the published sample.
 */
class RequestFirmOffer(
    private val repository: OfferRepository,
) {
    suspend fun submit(line: QuoteLine, answers: QuoteAnswers): QuoteAttempt {
        val risk = riskOf(line, answers) ?: return QuoteAttempt.Gap(missing)
        return QuoteAttempt.Answer(repository.quote(line.ramo, risk))
    }

    private var missing: QuoteInput = QuoteInput.Value

    private fun riskOf(line: QuoteLine, answers: QuoteAnswers): LineRisk? = when (line) {
        QuoteLine.Device -> {
            val value = positive(answers.value, QuoteInput.Value) ?: return null
            val brand = text(answers.brand, QuoteInput.Brand) ?: return null
            val older = answers.olderThan12Months ?: return gap(QuoteInput.Age)
            DeviceRisk(value, brand, older)
        }
        QuoteLine.Life -> {
            val sum = positive(answers.sumInsured, QuoteInput.SumInsured) ?: return null
            val age = positive(answers.ageYears, QuoteInput.AgeYears) ?: return null
            LifeRisk(sum, age)
        }
        QuoteLine.Climate -> {
            val event = text(answers.event, QuoteInput.Event) ?: return null
            val reference = text(answers.reference, QuoteInput.Reference) ?: return null
            val threshold = positive(answers.threshold, QuoteInput.Threshold) ?: return null
            ClimateRisk(event, reference, threshold)
        }
        QuoteLine.Mortgage -> {
            val value = positive(answers.creditValue, QuoteInput.CreditValue) ?: return null
            val term = positive(answers.creditTerm, QuoteInput.CreditTerm) ?: return null
            MortgageRisk(value, term)
        }
        QuoteLine.Payments -> {
            val installment = positive(answers.installment, QuoteInput.Installment) ?: return null
            val term = positive(answers.term, QuoteInput.Term) ?: return null
            PaymentsRisk(installment, term)
        }
        QuoteLine.Travel -> {
            val destination = text(answers.destination, QuoteInput.Destination) ?: return null
            val duration = positive(answers.duration, QuoteInput.Duration) ?: return null
            TravelRisk(destination, duration)
        }
    }

    private fun text(raw: String, field: QuoteInput): String? {
        val trimmed = raw.trim()
        if (trimmed.isEmpty()) return gap(field)
        return trimmed
    }

    private fun positive(raw: String, field: QuoteInput): Long? {
        val value = raw.trim().toLongOrNull()
        if (value == null || value <= 0L) return gap(field)
        return value
    }

    private fun gap(field: QuoteInput): Nothing? {
        missing = field
        return null
    }
}
