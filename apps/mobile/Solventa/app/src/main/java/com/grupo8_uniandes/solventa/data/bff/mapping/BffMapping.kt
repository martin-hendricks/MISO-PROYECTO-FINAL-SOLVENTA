package com.grupo8_uniandes.solventa.data.bff.mapping

import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceInDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.AttachmentKindDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimReceiptDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimStatusDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimsDto
import com.grupo8_uniandes.solventa.data.bff.dto.DetailDto
import com.grupo8_uniandes.solventa.data.bff.dto.HomeDto
import com.grupo8_uniandes.solventa.data.bff.dto.IssuedDto
import com.grupo8_uniandes.solventa.data.bff.dto.LivenessDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageInDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageOutDto
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
import com.grupo8_uniandes.solventa.data.bff.dto.WalletDto
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceResult
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
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
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.domain.bff.mortgage.CreditProfile
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageQuote
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityNotice
import com.grupo8_uniandes.solventa.domain.bff.offer.DeviceRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.payment.AutomaticPayment
import com.grupo8_uniandes.solventa.domain.bff.push.PushDestination
import com.grupo8_uniandes.solventa.domain.bff.push.PushNotice
import com.grupo8_uniandes.solventa.domain.bff.push.PushRegistration
import com.grupo8_uniandes.solventa.domain.bff.push.PushType
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import com.grupo8_uniandes.solventa.domain.bff.signup.ConsentRevocation
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRecord
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json

private val json = Json

internal inline fun <reified T> decode(raw: String): T? =
    try {
        json.decodeFromString<T>(raw)
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
)

internal fun RevokeDto.toRevocation() = ConsentRevocation(habeasData)

internal fun OfferInDto.toRisk() = DeviceRisk(
    datosRiesgo.valorDispositivo,
    datosRiesgo.marca,
    datosRiesgo.masDe12Meses,
)

internal fun OfferOutDto.toOffer() = FirmOffer(cotizacionId, ramo, estado, prima, moneda, venceEn)

internal fun IssuedDto.toPolicy() = IssuedPolicy(numero, ramo, estado, venceEn)

internal fun RejectionDto.toRejection(): IssueRejection? =
    if (estado == "rechazada") IssueRejection(estado, motivo) else null

internal fun WalletDto.toEntries() = polizas.map {
    WalletEntry(it.numero, it.ramo, it.resumen, it.estado, it.venceEn)
}

internal fun DetailDto.toDetail() = PolicyDetail(numero, ramo, resumen, estado, venceEn, queHacer)

internal fun ClaimNoticeDto.toNotice() = ClaimNotice(
    poliza,
    fechaHecho,
    geo?.let { GeoPoint(it.lat, it.lng, it.precisionM) },
    adjuntos.map { Attachment(it.tipo.toKind(), it.nombre) },
)

internal fun ClaimReceiptDto.toReceipt() = ClaimReceipt(siniestroId, estado.toStatus())

internal fun ClaimsDto.toSummaries() = siniestros.map {
    ClaimSummary(it.siniestroId, it.ramo, it.resumen, it.estado.toStatus())
}

internal fun PaymentDto.toPayment() = AutomaticPayment(siniestroId, poliza, umbral, monto, moneda, estado)

internal fun MortgageInDto.toProfile() = CreditProfile(credito.valor, credito.plazoMeses, consentimientoPerfil)

internal fun MortgageOutDto.toQuote() = MortgageQuote(ramo, estado, prima, moneda, factores, degradada)

internal fun NoticesDto.toNotices() = avisos.map { ValidityNotice(it.tipo, it.poliza, it.venceEn, it.estado) }

internal fun PolicyCommandDto.toPolicyOrNull(issued: IssuedPolicy): IssuedPolicy? =
    if (verbo == PolicyVerbDto.cancelar && motivo.isNullOrBlank()) null else issued

internal fun HomeDto.toHome() = BffHome(
    HomeOfferSlot(ofertaVigente.cotizacionId, ofertaVigente.ramo, ofertaVigente.estado),
    HomePolicySlot(poliza.numero, poliza.ramo, poliza.estado),
    HomeClaimSlot(siniestroEnCurso.siniestroId, siniestroEnCurso.estado),
    hipotecario,
)

internal fun PushRegistrationDto.toRegistration() = PushRegistration(token, plataforma)

internal fun PushNoticeDto.toNotice() = PushNotice(
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
    PushTypeDto.pago_automatico -> PushType.PAGO_AUTOMATICO
    PushTypeDto.vencimiento -> PushType.VENCIMIENTO
    PushTypeDto.renovacion -> PushType.RENOVACION
    PushTypeDto.estado_siniestro -> PushType.ESTADO_SINIESTRO
}

private fun PushDestinationDto.toDestination() = when (this) {
    PushDestinationDto.parametrico -> PushDestination.PARAMETRICO
    PushDestinationDto.`aviso-vencimiento` -> PushDestination.AVISO_VENCIMIENTO
    PushDestinationDto.`aviso-renovacion` -> PushDestination.AVISO_RENOVACION
    PushDestinationDto.`detalle-siniestro` -> PushDestination.DETALLE_SINIESTRO
}
