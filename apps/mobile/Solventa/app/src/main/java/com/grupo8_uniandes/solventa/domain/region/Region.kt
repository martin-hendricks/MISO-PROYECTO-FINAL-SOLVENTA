package com.grupo8_uniandes.solventa.domain.region

enum class Region(val languageTag: String, val currencyCode: String) {
    Colombia("es-CO", "COP"),
    Mexico("es-MX", "MXN"),
    Chile("es-CL", "CLP"),
    Peru("es-PE", "PEN"),
    ;

    companion object {
        fun fromStored(tag: String?): Region =
            entries.firstOrNull { it.languageTag == tag } ?: Colombia
    }
}
