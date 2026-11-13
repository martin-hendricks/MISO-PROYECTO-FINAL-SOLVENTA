package com.grupo8_uniandes.solventa.data.bff.mapping

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

import com.grupo8_uniandes.solventa.data.bff.dto.BilleteraDto
import com.grupo8_uniandes.solventa.data.bff.dto.MovimientoDto
import com.grupo8_uniandes.solventa.data.bff.dto.AcceptedQuoteDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceInDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceGeoDto
import com.grupo8_uniandes.solventa.data.bff.dto.AttachmentDto
import com.grupo8_uniandes.solventa.data.bff.dto.AttachmentKindDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimDetailDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimReceiptDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimSummaryDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimStatusDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimsDto
import com.grupo8_uniandes.solventa.data.bff.dto.CreditDto
import com.grupo8_uniandes.solventa.data.bff.dto.DetailDto
import com.grupo8_uniandes.solventa.data.bff.dto.DeviceRiskDto
import com.grupo8_uniandes.solventa.data.bff.dto.GeoDto
import com.grupo8_uniandes.solventa.data.bff.dto.HomeDto
import com.grupo8_uniandes.solventa.data.bff.dto.IssuedDto
import com.grupo8_uniandes.solventa.data.bff.dto.LivenessDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageInDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.ProfilingConsentDto
import com.grupo8_uniandes.solventa.data.bff.dto.NoticesDto
import com.grupo8_uniandes.solventa.data.bff.dto.OfferInDto
import com.grupo8_uniandes.solventa.data.bff.dto.OfferOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.PaymentDto
import com.grupo8_uniandes.solventa.data.bff.dto.PolicyCommandDto
import com.grupo8_uniandes.solventa.data.bff.dto.PolicyVerbDto
import com.grupo8_uniandes.solventa.data.bff.dto.ProvidersDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushDestinationDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushRegistrationDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushTypeDto
import com.grupo8_uniandes.solventa.data.bff.dto.RejectionDto
import com.grupo8_uniandes.solventa.data.bff.dto.RevokeDto
import com.grupo8_uniandes.solventa.data.bff.dto.SessionOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.SignupDto
import com.grupo8_uniandes.solventa.data.bff.dto.PoliciesDto
import com.grupo8_uniandes.solventa.data.bff.dto.PolicyEntryDto
import com.grupo8_uniandes.solventa.domain.bff.billetera.Deposit
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositType
import com.grupo8_uniandes.solventa.domain.bff.billetera.Wallet
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceResult
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimDetail
import com.grupo8_uniandes.solventa.domain.bff.claim.EvidenceBytes
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimEvidence
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimHistory
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimPayment
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.domain.bff.home.BffHome
import com.grupo8_uniandes.solventa.domain.bff.home.HomeClaimSlot
import com.grupo8_uniandes.solventa.domain.bff.home.HomeOfferSlot
import com.grupo8_uniandes.solventa.domain.bff.home.HomePolicySlot
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssueRejection
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuedPolicy
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyCancellation
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyCoverage
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import com.grupo8_uniandes.solventa.domain.bff.mortgage.CreditProfile
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageQuote
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ProfilingConsent
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityNotice
import com.grupo8_uniandes.solventa.domain.bff.offer.AcceptedQuote
import com.grupo8_uniandes.solventa.domain.bff.offer.ClimateRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.DeviceRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.LifeRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.MortgageRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.PaymentsRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.SoatRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.TravelRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.payment.AutomaticPayment
import com.grupo8_uniandes.solventa.domain.bff.push.NoticeDestination
import com.grupo8_uniandes.solventa.domain.bff.push.NoticeEntry
import com.grupo8_uniandes.solventa.domain.bff.push.NoticeKind
import com.grupo8_uniandes.solventa.domain.bff.push.PushRegistration
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import com.grupo8_uniandes.solventa.domain.bff.signup.ConsentRevocation
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRecord
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.encodeToJsonElement
import kotlinx.serialization.json.put

internal val bffJson = Json {
    ignoreUnknownKeys = true
    encodeDefaults = true
    explicitNulls = true
}

internal inline fun <reified T> decode(raw: String): T? =
    try {
        bffJson.decodeFromString<T>(raw)
    } catch (_: SerializationException) {
        null
    }

internal fun <T> required(value: T?): T = value ?: throw SerializationException("missing")

internal fun SessionOutDto.toTokens() = SessionTokens(accessToken, refreshToken, expiraEn)

internal fun SignupDto.toRecord() = SignupRecord(
    nombre,
    apellidos,
    documento,
    correo,
    if (pruebaDeVida == LivenessDto.ok) Liveness.OK else Liveness.NO,
    habeasData,
    tipoDocumento = tipoDocumento,
    ingresosMensuales = ingresosMensuales,
    gastosMensuales = gastosMensuales,
)

internal fun RevokeDto.toRevocation() = ConsentRevocation(habeasData)

internal fun OfferInDto.toRisk() = DeviceRisk(
    datosRiesgo.valorDispositivo,
    datosRiesgo.marca,
    datosRiesgo.masDe12Meses,
    datosRiesgo.modelo,
)

internal fun LineRisk.toRequestElement(): JsonElement = when (this) {
    is DeviceRisk -> bffJson.encodeToJsonElement(DeviceRiskDto(valorDispositivo, marca, masDe12Meses, modelo))
    is LifeRisk -> buildJsonObject {
        put("sumaAsegurada", sumInsured)
        put("edad", ageYears)
    }
    is ClimateRisk -> buildJsonObject {
        put("evento", event)
        if (reference.isNotBlank()) put("referencia", reference)
        put("umbral", threshold)
    }
    is MortgageRisk -> buildJsonObject {
        put("valor", creditValue)
        put("plazoMeses", termMonths)
    }
    is PaymentsRisk -> buildJsonObject {
        put("cuota", installment)
        put("plazoMeses", termMonths)
    }
    is TravelRisk -> buildJsonObject {
        put("destino", destination)
        put("duracion", duration)
    }
    is SoatRisk -> buildJsonObject {
        put("cilindraje_cc", displacement)
        put("modelo_anio", modelYear)
        put("ciudad_circulacion", city)
    }
}

internal fun SignupRecord.toDto() = SignupDto(
    nombre,
    apellidos,
    documento,
    correo,
    if (pruebaDeVida == Liveness.OK) LivenessDto.ok else LivenessDto.no,
    habeasData,
    contrasena,
    tipoDocumento,
    ingresosMensuales,
    gastosMensuales,
)

internal fun ClaimNotice.toDto() = ClaimNoticeDto(
    poliza,
    fechaHecho,
    geo?.let { GeoDto(it.lat, it.lng, it.precisionM) },
    adjuntos.map { AttachmentDto(it.tipo.toDto(), it.nombre) },
    descripcion,
    lugar,
)

internal fun CreditProfile.toDto() = MortgageInDto(CreditDto(valor, plazoMeses), consentimientoPerfil)

internal fun PushRegistration.toDto() = PushRegistrationDto(token, plataforma)

internal fun AssistanceRequest.toDto() = AssistanceInDto(prestadorId, AssistanceGeoDto(lat, lng), poliza)

internal fun List<PolicyEntry>.toDto() = PoliciesDto(
    map { PolicyEntryDto(it.numero, it.ramo, it.resumen, it.estado, it.venceEn) },
)

private fun AttachmentKind.toDto() = when (this) {
    AttachmentKind.FOTO -> AttachmentKindDto.foto
    AttachmentKind.VIDEO -> AttachmentKindDto.video
    AttachmentKind.RECIBO -> AttachmentKindDto.recibo
    AttachmentKind.SOPORTE -> AttachmentKindDto.soporte
}

internal fun OfferOutDto.toOffer() = FirmOffer(cotizacionId, ramo, estado, prima, moneda, venceEn)

internal fun AcceptedQuoteDto.toAccepted() = AcceptedQuote(cotizacionId, estado, prima, moneda)

internal fun IssuedDto.toPolicy() = IssuedPolicy(numero, ramo, estado, venceEn)

internal fun RejectionDto.toRejection(): IssueRejection? =
    if (estado == "rechazada") IssueRejection(estado, motivo) else null

internal fun PoliciesDto.toEntries() = polizas.map {
    PolicyEntry(it.numero, it.ramo, it.resumen, it.estado, it.venceEn)
}

internal fun DetailDto.toDetail() = PolicyDetail(
    numero,
    ramo,
    resumen,
    estado,
    venceEn,
    queHacer,
    inicioVigencia,
    finVigencia,
    moneda,
    primaTotal,
    coberturas.map { PolicyCoverage(it.nombre, it.sumaAsegurada, it.deducible) },
    renovable,
    renovacionAutomatica,
    cancelacion?.let { PolicyCancellation(it.motivo, it.canceladaEn, it.devolucionEstimada) },
)

internal fun ClaimNoticeDto.toNotice() = ClaimNotice(
    poliza,
    fechaHecho,
    geo?.let { GeoPoint(it.lat, it.lng, it.precisionM) },
    adjuntos.map { Attachment(it.tipo.toKind(), it.nombre) },
    descripcion,
    lugar,
)

internal fun ClaimReceiptDto.toReceipt() = ClaimReceipt(siniestroId, estado.toStatus())

internal fun ClaimsDto.toSummaries() = siniestros.map { it.toSummary() }

internal fun ClaimSummaryDto.toSummary() = ClaimSummary(
    siniestroId,
    ramo,
    resumen,
    estado.toStatus(),
    estadoTexto,
    id ?: siniestroId,
    tipo ?: "asistido",
    fecha,
    reserva,
    moneda,
    poliza,
    resultado,
)

internal fun ClaimDetailDto.toDetail() = ClaimDetail(
    summary = ClaimSummary(
        siniestroId,
        ramo,
        resumen,
        estado.toStatus(),
        estadoTexto,
        id.ifBlank { siniestroId },
        tipo,
        fecha,
        reserva,
        moneda,
        poliza,
        resultado,
    ),
    poliza = poliza,
    descripcion = descripcion,
    lugar = lugar,
    geo = geo?.let { GeoPoint(it.lat, it.lng, it.precisionM) },
    motivo = motivo,
    evidencia = evidencia.map { ClaimEvidence(it.nombre, it.tipo, it.contentType, it.url) },
    historial = historial.map { ClaimHistory(it.estado, it.fecha, it.estadoTexto) },
    pago = pago?.let { ClaimPayment(it.comprobante, it.monto, it.moneda, it.fecha) },
    umbral = umbral,
)

internal fun PaymentDto.toPayment() = AutomaticPayment(siniestroId, poliza, umbral, monto, moneda, estado)

internal fun MortgageInDto.toProfile() = CreditProfile(credito.valor, credito.plazoMeses, consentimientoPerfil)

internal fun MortgageOutDto.toQuote() = MortgageQuote(ramo, estado, prima, moneda, factores, degradada)

internal fun ProfilingConsentDto.toProfilingConsent(): ProfilingConsent = when (estado) {
    "vigente" -> ProfilingConsent.Granted(required(otorgadoEn))
    "revocado" -> ProfilingConsent.Revoked(required(revocadoEn))
    "sin_consentimiento" -> ProfilingConsent.None
    else -> throw SerializationException("estado")
}

internal fun NoticesDto.toNotices() = avisos.map { ValidityNotice(it.tipo, it.poliza, it.venceEn, it.estado) }

internal fun PolicyCommandDto.toPolicyOrNull(issued: IssuedPolicy): IssuedPolicy? =
    if (verbo == PolicyVerbDto.cancelar && motivo.isNullOrBlank()) null else issued

internal fun HomeDto.toHome() = BffHome(
    ofertaVigente?.let { HomeOfferSlot(it.cotizacionId, it.ramo, it.estado) },
    poliza?.let { HomePolicySlot(it.numero, it.ramo, it.estado) },
    siniestroEnCurso?.let { HomeClaimSlot(it.siniestroId, it.estado) },
    hipotecario,
    cotizacionesPendientes.map { HomeOfferSlot(it.cotizacionId, it.ramo, it.estado) },
)

internal fun PushRegistrationDto.toRegistration() = PushRegistration(token, plataforma)

internal fun PushNoticeDto.toNotice() = NoticeEntry(
    tipo.toType(),
    titulo,
    cuerpo,
    destino.toDestination(),
    poliza,
)

internal fun ProvidersDto.toProviders() = prestadores.map {
    Provider(it.id, it.nombre, it.distanciaKm, it.zona)
}

internal fun AssistanceInDto.toRequest() = AssistanceRequest(prestadorId, geo.lat, geo.lng, poliza)

internal fun AssistanceOutDto.toResult() = AssistanceResult(asistenciaId, estado)

internal fun ClaimNotice.toParts(): List<MultipartBody.Part> {
    val parts = mutableListOf(
        MultipartBody.Part.createFormData("poliza", poliza),
        MultipartBody.Part.createFormData("fechaHecho", fechaHecho),
        MultipartBody.Part.createFormData("descripcion", descripcion),
    )
    if (lugar.isNotBlank()) parts += MultipartBody.Part.createFormData("lugar", lugar)
    geo?.let {
        val json = """{"lat":${it.lat},"lng":${it.lng},"precisionM":${it.precisionM}}"""
        parts += MultipartBody.Part.createFormData("geo", json)
    }
    adjuntos.forEach { file ->
        val type = file.contentType.toMediaType()
        val bytes = EvidenceBytes.read(file.nombre) ?: file.nombre.toByteArray()
        parts += MultipartBody.Part.createFormData(
            "archivos",
            file.nombre,
            bytes.toRequestBody(type),
        )
    }
    return parts
}

private fun AttachmentKindDto.toKind() = when (this) {
    AttachmentKindDto.foto -> AttachmentKind.FOTO
    AttachmentKindDto.video -> AttachmentKind.VIDEO
    AttachmentKindDto.recibo -> AttachmentKind.RECIBO
    AttachmentKindDto.soporte -> AttachmentKind.SOPORTE
}

private fun ClaimStatusDto.toStatus() = when (this) {
    ClaimStatusDto.recibido -> ClaimStatus.RECIBIDO
    ClaimStatusDto.en_evaluacion -> ClaimStatus.EN_EVALUACION
    ClaimStatusDto.decidido -> ClaimStatus.DECIDIDO
    ClaimStatusDto.enrutado -> ClaimStatus.ENRUTADO
    ClaimStatusDto.pagado -> ClaimStatus.PAGADO
}

private fun PushTypeDto.toType() = when (this) {
    PushTypeDto.pago_automatico -> NoticeKind.PAGO_AUTOMATICO
    PushTypeDto.vencimiento -> NoticeKind.VENCIMIENTO
    PushTypeDto.renovacion -> NoticeKind.RENOVACION
    PushTypeDto.estado_siniestro -> NoticeKind.ESTADO_SINIESTRO
}

internal fun BilleteraDto.toWallet() = Wallet(
    moneda,
    totalRecibido,
    movimientos.map { it.toDeposit() },
)

internal fun MovimientoDto.toDeposit() = Deposit(
    id,
    siniestroId,
    if (tipo == "pago_automatico") DepositType.Automatic else DepositType.Assisted,
    ramo,
    resumen,
    poliza,
    monto,
    moneda,
    comprobante,
    depositadoEn,
)

internal fun Wallet.toDto() = BilleteraDto(
    moneda,
    totalRecibido,
    movimientos.map { it.toDto() },
)

internal fun Deposit.toDto() = MovimientoDto(
    id,
    siniestroId,
    if (tipo == DepositType.Automatic) "pago_automatico" else "asistido",
    ramo,
    resumen,
    poliza,
    monto,
    moneda,
    comprobante,
    depositadoEn,
)

private fun PushDestinationDto.toDestination() = when (this) {
    PushDestinationDto.parametrico -> NoticeDestination.PARAMETRICO
    PushDestinationDto.`aviso-vencimiento` -> NoticeDestination.AVISO_VENCIMIENTO
    PushDestinationDto.`aviso-renovacion` -> NoticeDestination.AVISO_RENOVACION
    PushDestinationDto.`detalle-siniestro` -> NoticeDestination.DETALLE_SINIESTRO
}
