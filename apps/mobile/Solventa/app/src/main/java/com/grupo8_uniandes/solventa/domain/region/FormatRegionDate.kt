package com.grupo8_uniandes.solventa.domain.region

import java.text.SimpleDateFormat
import java.time.LocalDate
import java.time.ZoneOffset
import java.util.Date
import java.util.Locale
import java.util.TimeZone

fun formatRegionDate(date: LocalDate, region: Region): String {
    val pattern = when (region) {
        Region.Colombia -> "dd/MM/yyyy"
        Region.Mexico -> "MM/dd/yyyy"
        Region.Chile -> "dd-MM-yyyy"
        Region.Peru -> "dd/MM/yyyy"
    }
    val format = SimpleDateFormat(pattern, Locale.forLanguageTag(region.languageTag))
    format.timeZone = TimeZone.getTimeZone("UTC")
    val instant = date.atStartOfDay(ZoneOffset.UTC).toInstant()
    return format.format(Date.from(instant))
}
