package com.grupo8_uniandes.solventa.domain.region

import java.math.BigDecimal
import java.math.RoundingMode
import java.text.DecimalFormat
import java.text.NumberFormat
import java.util.Locale

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
