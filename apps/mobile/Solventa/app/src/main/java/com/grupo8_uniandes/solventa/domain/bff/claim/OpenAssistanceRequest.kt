package com.grupo8_uniandes.solventa.domain.bff.claim

data class AssistanceForm(
    val registration: String,
    val policyValue: String,
    val dateValue: String,
    val descriptionValue: String,
    val placeValue: String,
)

class OpenAssistanceRequest {
    private var openedCount: Int = 0

    fun open(locationAllowed: Boolean): AssistanceForm? {
        if (!locationAllowed || openedCount > 0) return null
        openedCount += 1
        return AssistanceForm(
            registration = "Registramos el pedido con tu ubicación. Operaciones lo ve; no hay despacho real a un taller.",
            policyValue = "POL-88219-CO · Protección de dispositivo",
            dateValue = "12 mar 2026",
            descriptionValue = "Pantalla rota al caer el teléfono",
            placeValue = "Av. Caracas con Calle 72",
        )
    }

    fun cancel() = Unit

    fun openedCount(): Int = openedCount
}
