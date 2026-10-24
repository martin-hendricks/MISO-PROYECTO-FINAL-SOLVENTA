package com.grupo8_uniandes.solventa.data.bff.dto

import kotlinx.serialization.Serializable

@Serializable
data class SessionInDto(val correo: String, val contrasena: String)

@Serializable
data class SessionOutDto(val accessToken: String, val refreshToken: String, val expiraEn: Int)

@Serializable
data class RefreshInDto(val refreshToken: String)

@Serializable
enum class LivenessDto { ok, no }

@Serializable
data class SignupDto(
    val nombre: String,
    val apellidos: String,
    val documento: String,
    val correo: String,
    val pruebaDeVida: LivenessDto,
    val habeasData: Boolean,
)

@Serializable
data class RevokeDto(val habeasData: Boolean)

@Serializable
data class DeviceRiskDto(
    val valorDispositivo: Long,
    val marca: String,
    val masDe12Meses: Boolean,
)

@Serializable
data class OfferInDto(val ramo: String, val datosRiesgo: DeviceRiskDto)

@Serializable
data class OfferOutDto(
    val cotizacionId: String,
    val ramo: String,
    val estado: String,
    val prima: Long,
    val moneda: String,
    val venceEn: String,
)

@Serializable
data class IdDto(val cotizacionId: String)

@Serializable
data class IssuedDto(
    val numero: String,
    val ramo: String,
    val estado: String,
    val venceEn: String,
)

@Serializable
data class RejectionDto(val estado: String, val motivo: String)

@Serializable
data class WalletEntryDto(
    val numero: String,
    val ramo: String,
    val resumen: String,
    val estado: String,
    val venceEn: String,
)

@Serializable
data class WalletDto(val polizas: List<WalletEntryDto>)

@Serializable
data class DetailDto(
    val numero: String,
    val ramo: String,
    val resumen: String,
    val estado: String,
    val venceEn: String,
    val queHacer: String,
)

@Serializable
data class GeoDto(val lat: Double, val lng: Double, val precisionM: Int)

@Serializable
enum class AttachmentKindDto { foto, video, recibo, soporte }

@Serializable
data class AttachmentDto(val tipo: AttachmentKindDto, val nombre: String)

@Serializable
data class ClaimNoticeDto(
    val poliza: String,
    val fechaHecho: String,
    val geo: GeoDto? = null,
    val adjuntos: List<AttachmentDto>,
)

@Serializable
enum class ClaimStatusDto { recibido, en_evaluacion, decidido, enrutado, pagado }

@Serializable
data class ClaimReceiptDto(val siniestroId: String, val estado: ClaimStatusDto)

@Serializable
data class ClaimSummaryDto(
    val siniestroId: String,
    val ramo: String,
    val resumen: String,
    val estado: ClaimStatusDto,
)

@Serializable
data class ClaimsDto(val siniestros: List<ClaimSummaryDto>)

@Serializable
data class PaymentDto(
    val siniestroId: String,
    val poliza: String,
    val umbral: String,
    val monto: Long,
    val moneda: String,
    val estado: String,
)

@Serializable
data class CreditDto(val valor: Long, val plazoMeses: Int)

@Serializable
data class MortgageInDto(val credito: CreditDto, val consentimientoPerfil: Boolean)

@Serializable
data class MortgageOutDto(
    val ramo: String,
    val estado: String,
    val prima: Long,
    val moneda: String,
    val factores: List<String>,
    val degradada: Boolean,
)

@Serializable
data class NoticeDto(
    val tipo: String,
    val poliza: String,
    val venceEn: String? = null,
    val estado: String? = null,
)

@Serializable
data class NoticesDto(val avisos: List<NoticeDto>)

@Serializable
enum class PolicyVerbDto { renovar, modificar, cancelar }

@Serializable
data class PolicyCommandDto(
    val numero: String,
    val verbo: PolicyVerbDto,
    val motivo: String? = null,
)

@Serializable
data class HomeOfferDto(val cotizacionId: String, val ramo: String, val estado: String)

@Serializable
data class HomePolicyDto(val numero: String, val ramo: String, val estado: String)

@Serializable
data class HomeClaimDto(val siniestroId: String, val estado: String)

@Serializable
data class HomeDto(
    val ofertaVigente: HomeOfferDto,
    val poliza: HomePolicyDto,
    val siniestroEnCurso: HomeClaimDto,
    val hipotecario: String? = null,
)

@Serializable
data class PushRegistrationDto(val token: String, val plataforma: String)

@Serializable
enum class PushTypeDto { pago_automatico, vencimiento, renovacion, estado_siniestro }

@Serializable
enum class PushDestinationDto {
    parametrico,
    `aviso-vencimiento`,
    `aviso-renovacion`,
    `detalle-siniestro`,
}

@Serializable
data class PushNoticeDto(
    val tipo: PushTypeDto,
    val titulo: String,
    val cuerpo: String,
    val destino: PushDestinationDto,
    val poliza: String,
)

@Serializable
data class ProviderDto(
    val id: String,
    val nombre: String,
    val distanciaKm: Double,
    val zona: String,
)

@Serializable
data class ProvidersDto(val prestadores: List<ProviderDto>)

@Serializable
data class AssistanceGeoDto(val lat: Double, val lng: Double)

@Serializable
data class AssistanceInDto(
    val prestadorId: String,
    val geo: AssistanceGeoDto,
    val poliza: String,
)

@Serializable
data class AssistanceOutDto(val asistenciaId: String, val estado: String)
