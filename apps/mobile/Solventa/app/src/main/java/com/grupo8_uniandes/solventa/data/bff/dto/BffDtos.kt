package com.grupo8_uniandes.solventa.data.bff.dto

import kotlinx.serialization.KSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerializationException
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.json.JsonDecoder
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonEncoder
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonPrimitive
import java.math.BigDecimal
import java.math.RoundingMode

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
    val contrasena: String = "",
    val tipoDocumento: String = "",
    @kotlinx.serialization.SerialName("ingresos_mensuales") val ingresosMensuales: String = "",
    @kotlinx.serialization.SerialName("gastos_mensuales") val gastosMensuales: String = "",
)

@Serializable
data class RenewalRequestDto(val renovacionAutomatica: Boolean)

@Serializable
data class RenewalPreferenceDto(val numero: String, val renovacionAutomatica: Boolean)

@Serializable
data class RevokeDto(val habeasData: Boolean)

@Serializable
data class DeviceRiskDto(
    val valorDispositivo: Long,
    val marca: String,
    val masDe12Meses: Boolean,
    val modelo: String,
)

@Serializable
data class OfferInDto(val ramo: String, val datosRiesgo: DeviceRiskDto)

@Serializable
data class QuoteRequestDto(val ramo: String, val datosRiesgo: JsonElement)

@Serializable
data class OfferOutDto(
    val cotizacionId: String,
    val ramo: String,
    val estado: String,
    @Serializable(with = PesosSerializer::class)
    val prima: Long,
    val moneda: String,
    val venceEn: String,
)

/** Whole pesos from a JSON number or a decimal string such as `"106900.00"`. */
object PesosSerializer : KSerializer<Long> {
    override val descriptor: SerialDescriptor = JsonElement.serializer().descriptor

    override fun serialize(encoder: Encoder, value: Long) {
        val jsonEncoder = encoder as? JsonEncoder
        if (jsonEncoder == null) {
            encoder.encodeLong(value)
        } else {
            jsonEncoder.encodeJsonElement(JsonPrimitive(value))
        }
    }

    override fun deserialize(decoder: Decoder): Long {
        val element = (decoder as? JsonDecoder)?.decodeJsonElement()
            ?: return decoder.decodeLong()
        val raw = element.jsonPrimitive.content
        val pesos = try {
            BigDecimal(raw).setScale(0, RoundingMode.HALF_UP).longValueExact()
        } catch (error: NumberFormatException) {
            throw SerializationException("prima", error)
        } catch (error: ArithmeticException) {
            throw SerializationException("prima", error)
        }
        return pesos
    }
}

/** COP amounts stay exact. JSON may send a number or a decimal string. */
object DecimalSerializer : KSerializer<BigDecimal> {
    override val descriptor: SerialDescriptor = JsonElement.serializer().descriptor

    override fun serialize(encoder: Encoder, value: BigDecimal) {
        val jsonEncoder = encoder as? JsonEncoder
        if (jsonEncoder == null) encoder.encodeString(value.toPlainString())
        else jsonEncoder.encodeJsonElement(JsonPrimitive(value.toPlainString()))
    }

    override fun deserialize(decoder: Decoder): BigDecimal {
        val raw = (decoder as? JsonDecoder)?.decodeJsonElement()?.jsonPrimitive?.content
            ?: decoder.decodeString()
        return try {
            BigDecimal(raw)
        } catch (error: NumberFormatException) {
            throw SerializationException("monto", error)
        }
    }
}

@Serializable
data class AcceptedQuoteDto(
    val cotizacionId: String,
    val estado: String,
    @Serializable(with = PesosSerializer::class)
    val prima: Long,
    val moneda: String,
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
data class CoverageDto(
    val nombre: String,
    val sumaAsegurada: Double = 0.0,
    val deducible: Double = 0.0,
)

@Serializable
data class CancellationDto(
    val motivo: String? = null,
    val canceladaEn: String? = null,
    val devolucionEstimada: Double? = null,
)

@Serializable
data class PolicyEntryDto(
    val numero: String,
    val ramo: String,
    val resumen: String,
    val estado: String,
    val venceEn: String,
    val inicioVigencia: String? = null,
    val finVigencia: String? = null,
    val moneda: String? = null,
    val primaTotal: Double? = null,
    val coberturas: List<CoverageDto> = emptyList(),
)

@Serializable
data class PoliciesDto(val polizas: List<PolicyEntryDto>)

@Serializable
data class DetailDto(
    val numero: String,
    val ramo: String,
    val resumen: String,
    val estado: String,
    val venceEn: String,
    val queHacer: String,
    val inicioVigencia: String? = null,
    val finVigencia: String? = null,
    val moneda: String = "",
    val primaTotal: Double? = null,
    val coberturas: List<CoverageDto> = emptyList(),
    val renovable: Boolean = false,
    val renovacionAutomatica: Boolean = false,
    val cancelacion: CancellationDto? = null,
)

@Serializable
data class GeoDto(val lat: Double, val lng: Double, val precisionM: Int = 0)

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
    val descripcion: String = "",
    val lugar: String = "",
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
    val estadoTexto: String? = null,
    val id: String? = null,
    val tipo: String? = null,
    val fecha: String? = null,
    val reserva: Double? = null,
    val moneda: String? = null,
    val poliza: String? = null,
    val resultado: String? = null,
)

@Serializable
data class ClaimEvidenceDto(
    val nombre: String,
    val tipo: String,
    val contentType: String = "",
    val url: String = "",
)

@Serializable
data class ClaimHistoryDto(val estado: String, val fecha: String = "", val estadoTexto: String = "")

@Serializable
data class ClaimPaymentDto(
    val comprobante: String = "",
    val monto: Double = 0.0,
    val moneda: String = "",
    val fecha: String = "",
)

@Serializable
data class ClaimDetailDto(
    val id: String = "",
    val siniestroId: String,
    val tipo: String = "asistido",
    val ramo: String = "",
    val resumen: String = "",
    val fecha: String? = null,
    val estado: ClaimStatusDto,
    val estadoTexto: String? = null,
    val reserva: Double? = null,
    val moneda: String? = null,
    val poliza: String? = null,
    val descripcion: String? = null,
    val lugar: String? = null,
    val geo: GeoDto? = null,
    val motivo: String? = null,
    val evidencia: List<ClaimEvidenceDto> = emptyList(),
    val historial: List<ClaimHistoryDto> = emptyList(),
    val pago: ClaimPaymentDto? = null,
    val umbral: String? = null,
    val resultado: String? = null,
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
    val ofertaVigente: HomeOfferDto? = null,
    val poliza: HomePolicyDto? = null,
    val siniestroEnCurso: HomeClaimDto? = null,
    val hipotecario: String? = null,
    val cotizacionesPendientes: List<HomeOfferDto> = emptyList(),
)

@Serializable
data class PushRegistrationDto(val token: String, val plataforma: String)

@Serializable
data class PushTokenRetiroDto(val token: String)

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

@Serializable
data class MovimientoDto(
    val id: String,
    val siniestroId: String,
    val tipo: String,
    val ramo: String,
    val resumen: String = "",
    val poliza: String = "",
    @Serializable(with = DecimalSerializer::class) val monto: BigDecimal,
    val moneda: String,
    val comprobante: String,
    val depositadoEn: String,
)

@Serializable
data class BilleteraDto(
    val moneda: String,
    @Serializable(with = DecimalSerializer::class) val totalRecibido: BigDecimal,
    val movimientos: List<MovimientoDto>,
)
