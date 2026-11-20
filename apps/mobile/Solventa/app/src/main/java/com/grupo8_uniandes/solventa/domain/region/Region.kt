package com.grupo8_uniandes.solventa.domain.region

enum class Region(val languageTag: String, val currencyCode: String, val countryCode: String) {
    Colombia("es-CO", "COP", "CO"),
    Mexico("es-MX", "MXN", "MX"),
    Chile("es-CL", "CLP", "CL"),
    Peru("es-PE", "PEN", "PE"),
    ;

    companion object {
        fun fromStored(tag: String?): Region =
            entries.firstOrNull { it.languageTag == tag } ?: Colombia
    }
}
