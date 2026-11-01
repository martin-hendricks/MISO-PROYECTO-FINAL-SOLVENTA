package com.grupo8_uniandes.solventa.domain.registration

import com.grupo8_uniandes.solventa.domain.region.Region

fun documentTypes(region: Region): List<String> = when (region) {
    Region.Colombia -> listOf("CC", "CE", "PA")
    Region.Mexico -> listOf("INE", "CURP", "PA")
    Region.Chile -> listOf("RUT", "PA")
    Region.Peru -> listOf("DNI", "CE", "PA")
}
