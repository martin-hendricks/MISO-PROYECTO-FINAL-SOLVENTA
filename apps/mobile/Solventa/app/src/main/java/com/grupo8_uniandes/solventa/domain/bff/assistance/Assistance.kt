package com.grupo8_uniandes.solventa.domain.bff.assistance

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

enum class ProviderType(val code: String) {
    SERVICIO_TECNICO("servicio-tecnico"),
    TALLER_MOTOS("taller-motos"),
    IPS_URGENCIAS("ips-urgencias"),
    GRUA("grua"),
    ASISTENCIA_VIAJERO("asistencia-viajero"),
    PUNTO_AEROPUERTO("punto-aeropuerto"),
    IPS_EXAMENES("ips-examenes"),
    FUNERARIA("funeraria"),
    CENTRO_ATENCION("centro-atencion"),
}

data class Provider(
    val id: String,
    val nombre: String,
    val tipo: ProviderType,
    val ramos: List<String>,
    val direccion: String,
    val ciudad: String,
    val barrio: String,
    val lat: Double,
    val lng: Double,
    val telefono: String,
    val horario: String,
    val distanciaKm: Double?,
    val pais: String = "CO",
)

data class ProviderCenter(
    val lat: Double,
    val lng: Double,
    val origen: String,
)

data class ProviderCity(
    val nombre: String,
    val lat: Double,
    val lng: Double,
    val zoom: Int,
    val prestadores: Int,
)

data class ProviderArea(
    val norte: Double,
    val sur: Double,
    val este: Double,
    val oeste: Double,
)

data class ProviderQuery(
    val lat: Double? = null,
    val lng: Double? = null,
    val ramo: String? = null,
    val ciudad: String? = null,
    val radioKm: Double? = null,
    val pais: String? = null,
    val area: ProviderArea? = null,
)

data class ProviderPage(
    val centro: ProviderCenter?,
    val radioKm: Double?,
    val prestadores: List<Provider>,
    val truncado: Boolean = false,
)

data class ClaimProviders(
    val siniestroId: String,
    val numero: String,
    val ramo: String,
    val ramoFijo: String,
    val sinGeoetiqueta: Boolean,
    val centro: ProviderCenter?,
    val radioKm: Double?,
    val prestadores: List<Provider>,
    val truncado: Boolean = false,
)

data class AssistanceRequest(
    val prestadorId: String,
    val lat: Double,
    val lng: Double,
    val poliza: String,
)

data class AssistanceResult(
    val asistenciaId: String,
    val estado: String,
)

interface AssistanceRepository {
    suspend fun providers(query: ProviderQuery): StandInAnswer<ProviderPage>

    suspend fun cities(pais: String): StandInAnswer<List<ProviderCity>>

    suspend fun providersNearClaim(id: String, area: ProviderArea? = null): StandInAnswer<ClaimProviders>

    suspend fun request(body: AssistanceRequest): StandInAnswer<AssistanceResult>
}
