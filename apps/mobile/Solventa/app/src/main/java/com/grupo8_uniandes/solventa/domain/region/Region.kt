package com.grupo8_uniandes.solventa.domain.region

enum class Region(val languageTag: String) {
    Colombia("es-CO"),
    Mexico("es-MX"),
    Chile("es-CL"),
    Peru("es-PE"),
    ;

    companion object {
        fun fromStored(tag: String?): Region =
            entries.firstOrNull { it.languageTag == tag } ?: Colombia
    }
}
