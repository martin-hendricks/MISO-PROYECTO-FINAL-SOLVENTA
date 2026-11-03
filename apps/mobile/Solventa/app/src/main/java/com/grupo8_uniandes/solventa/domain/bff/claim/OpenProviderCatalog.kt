package com.grupo8_uniandes.solventa.domain.bff.claim

data class ProviderStub(
    val title: String,
    val body: String,
    val status: String,
)

sealed interface ProviderCatalog {
    data class Open(val rows: List<ProviderStub>) : ProviderCatalog

    data object Closed : ProviderCatalog
}

class OpenProviderCatalog {
    fun open(locationAllowed: Boolean): ProviderCatalog {
        if (!locationAllowed) return ProviderCatalog.Closed
        return ProviderCatalog.Open(
            listOf(
                ProviderStub("Taller Norte", "A 1,2 km · Chapinero", "En evaluación"),
                ProviderStub("Taller Sur", "A 3,4 km · Kennedy", "Pagado"),
                ProviderStub("SIN-P01", "Clima y vuelos · retraso de vuelo", "Pago automático · pagado"),
            ),
        )
    }
}
