package com.grupo8_uniandes.solventa.domain.bff.offer

import com.grupo8_uniandes.solventa.domain.region.Region
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale

/** Locale date for an ISO `venceEn`. The calendar day does not decide the offer status. */
fun formatOfferDate(isoDate: String, region: Region): String {
    val day = LocalDate.parse(isoDate)
    val formatter = DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM)
        .withLocale(Locale.forLanguageTag(region.languageTag))
    return day.format(formatter)
}
