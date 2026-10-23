package com.grupo8_uniandes.solventa.domain.bff.offer

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

enum class QuoteField { Value, Brand, Age }

sealed interface QuoteAttempt {
    data class Gap(val field: QuoteField) : QuoteAttempt

    data class Answer(val answer: StandInAnswer<FirmOffer>) : QuoteAttempt
}

/**
 * Asks the stand-in only after the three minimum answers are present.
 * The line is locked. The repository still returns the prepared offer.
 */
class RequestFirmOffer(
    private val repository: OfferRepository,
) {
    fun submit(valueText: String, brand: String, olderThan12Months: Boolean?): QuoteAttempt {
        val value = valueText.trim().toLongOrNull()
        if (value == null || value <= 0L) return QuoteAttempt.Gap(QuoteField.Value)
        if (brand.isBlank()) return QuoteAttempt.Gap(QuoteField.Brand)
        if (olderThan12Months == null) return QuoteAttempt.Gap(QuoteField.Age)
        return QuoteAttempt.Answer(
            repository.quote(
                LOCKED_LINE,
                DeviceRisk(
                    valorDispositivo = value,
                    marca = brand.trim(),
                    masDe12Meses = olderThan12Months,
                ),
            ),
        )
    }

    private companion object {
        const val LOCKED_LINE = "Protección de dispositivo"
    }
}
