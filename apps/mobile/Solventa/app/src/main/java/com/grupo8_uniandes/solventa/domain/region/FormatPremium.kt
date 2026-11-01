package com.grupo8_uniandes.solventa.domain.region

import java.math.BigDecimal
import java.math.RoundingMode
import java.text.DecimalFormat
import java.text.NumberFormat
import java.util.Locale

fun quoteAmountDigits(raw: String): String {
    val digits = raw.filter { it.isDigit() }
    if (digits.isEmpty()) return ""
    return digits.trimStart('0').ifEmpty { "0" }
}

fun formatQuoteAmount(digits: String, region: Region): String {
    val normalized = quoteAmountDigits(digits)
    if (normalized.isEmpty()) return ""
    val value = normalized.toLongOrNull() ?: return ""
    val number = NumberFormat.getNumberInstance(Locale.forLanguageTag(region.languageTag))
    number.minimumFractionDigits = 0
    number.maximumFractionDigits = 0
    val symbol = if (region == Region.Peru) "S/ " else "$"
    return symbol + number.format(value)
}

fun formatPremium(amount: BigDecimal, currencyCode: String, region: Region): String {
    val fractionDigits = when (currencyCode) {
        "COP", "CLP" -> 0
        else -> 2
    }
    val number = NumberFormat.getNumberInstance(Locale.forLanguageTag(region.languageTag))
    number.minimumFractionDigits = fractionDigits
    number.maximumFractionDigits = fractionDigits
    val formatted = number.halfUp().format(amount)
    val symbol = when (currencyCode) {
        "COP", "MXN", "CLP" -> "$"
        "PEN" -> "S/ "
        else -> ""
    }
    return symbol + formatted + " " + currencyCode
}

internal fun NumberFormat.halfUp(): NumberFormat {
    if (this is DecimalFormat) {
        roundingMode = RoundingMode.HALF_UP
    }
    return this
}
