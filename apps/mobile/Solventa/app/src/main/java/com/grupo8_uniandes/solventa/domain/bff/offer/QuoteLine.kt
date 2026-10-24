package com.grupo8_uniandes.solventa.domain.bff.offer

enum class QuoteLine(val ramo: String) {
    Device("Protección de dispositivo"),
    Life("Microseguro de vida"),
    Climate("Clima y vuelos"),
    Mortgage("Vida hipotecario"),
    Payments("Pagos"),
    Travel("Viaje"),
}

enum class QuoteInput {
    Value,
    Brand,
    Age,
    SumInsured,
    AgeYears,
    Event,
    Reference,
    Threshold,
    CreditValue,
    CreditTerm,
    Installment,
    Term,
    Destination,
    Duration,
}

data class QuoteAnswers(
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
)

data class LifeRisk(
    val sumInsured: Long,
    val ageYears: Long,
) : LineRisk

data class ClimateRisk(
    val event: String,
    val reference: String,
    val threshold: Long,
) : LineRisk

data class MortgageRisk(
    val creditValue: Long,
    val termMonths: Long,
) : LineRisk

data class PaymentsRisk(
    val installment: Long,
    val termMonths: Long,
) : LineRisk

data class TravelRisk(
    val destination: String,
    val duration: Long,
) : LineRisk
