package com.grupo8_uniandes.solventa.bff

import com.grupo8_uniandes.solventa.data.bff.MobileBff
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceGeoDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceInDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.AttachmentDto
import com.grupo8_uniandes.solventa.data.bff.dto.AttachmentKindDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimReceiptDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimStatusDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimSummaryDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimsDto
import com.grupo8_uniandes.solventa.data.bff.dto.CreditDto
import com.grupo8_uniandes.solventa.data.bff.dto.DetailDto
import com.grupo8_uniandes.solventa.data.bff.dto.DeviceRiskDto
import com.grupo8_uniandes.solventa.data.bff.dto.GeoDto
import com.grupo8_uniandes.solventa.data.bff.dto.HomeClaimDto
import com.grupo8_uniandes.solventa.data.bff.dto.HomeDto
import com.grupo8_uniandes.solventa.data.bff.dto.HomeOfferDto
import com.grupo8_uniandes.solventa.data.bff.dto.HomePolicyDto
import com.grupo8_uniandes.solventa.data.bff.dto.IssuedDto
import com.grupo8_uniandes.solventa.data.bff.dto.LivenessDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageInDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.NoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.NoticesDto
import com.grupo8_uniandes.solventa.data.bff.dto.OfferInDto
import com.grupo8_uniandes.solventa.data.bff.dto.OfferOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.PaymentDto
import com.grupo8_uniandes.solventa.data.bff.dto.ProviderDto
import com.grupo8_uniandes.solventa.data.bff.dto.ProvidersDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushDestinationDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushRegistrationDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushTypeDto
import com.grupo8_uniandes.solventa.data.bff.dto.RevokeDto
import com.grupo8_uniandes.solventa.data.bff.dto.SessionOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.WalletDto
import com.grupo8_uniandes.solventa.data.bff.dto.WalletEntryDto
import com.grupo8_uniandes.solventa.data.bff.dto.IdDto
import com.grupo8_uniandes.solventa.data.bff.dto.PolicyCommandDto
import com.grupo8_uniandes.solventa.data.bff.dto.PolicyVerbDto
import com.grupo8_uniandes.solventa.data.bff.dto.RefreshInDto
import com.grupo8_uniandes.solventa.data.bff.dto.RejectionDto
import com.grupo8_uniandes.solventa.data.bff.dto.SessionInDto
import com.grupo8_uniandes.solventa.data.bff.dto.SignupDto
import com.grupo8_uniandes.solventa.data.bff.fixture.PublishedSamples
import com.grupo8_uniandes.solventa.data.bff.mapping.decode
import com.grupo8_uniandes.solventa.data.bff.mapping.toDto
import com.grupo8_uniandes.solventa.data.bff.mapping.toNotice
import com.grupo8_uniandes.solventa.data.bff.mapping.toPolicyOrNull
import com.grupo8_uniandes.solventa.data.bff.mapping.toReceipt
import com.grupo8_uniandes.solventa.data.bff.mapping.toRecord
import com.grupo8_uniandes.solventa.data.bff.mapping.toRejection
import com.grupo8_uniandes.solventa.data.bff.mock.MockClaimRepository
import com.grupo8_uniandes.solventa.data.bff.mock.publishedAssistanceRequest
import com.grupo8_uniandes.solventa.data.bff.mock.publishedMortgageRequest
import com.grupo8_uniandes.solventa.data.bff.mock.publishedOfferRequest
import com.grupo8_uniandes.solventa.data.bff.mock.publishedSignup
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.push.PushDestination
import com.grupo8_uniandes.solventa.domain.bff.push.PushRegistration
import com.grupo8_uniandes.solventa.domain.bff.push.PushType
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.data.bff.mapping.toRequestElement
import com.grupo8_uniandes.solventa.domain.bff.offer.ClimateRisk
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import kotlinx.coroutines.runBlocking
import org.junit.Test

class SampleMappingTest {
    private val bff = MobileBff()

    @Test
    fun givenPublishedSamples_whenRead_thenValuesMatchTheContract() = runBlocking {
        val tokens = bff.session.signIn("camila@correo.com", "********").ready()
        assertEquals("jwt", tokens.accessToken)
        assertEquals("jwt", tokens.refreshToken)
        assertEquals(900, tokens.expiraEn)
        assertEquals(tokens, bff.session.refresh("jwt").ready())
        assertTrue(bff.session.signOut() is StandInAnswer.Ready)

        val signup = publishedSignup()!!
        assertEquals("Camila", signup.nombre)
        assertEquals("Restrepo", signup.apellidos)
        assertEquals("1012345678", signup.documento)
        assertEquals("camila@correo.com", signup.correo)
        assertEquals(Liveness.OK, signup.pruebaDeVida)
        assertEquals(true, signup.habeasData)
        assertEquals("Camila", bff.signup.register(signup).ready().nombre)
        assertEquals(false, bff.signup.revokeConsent().ready().habeasData)

        val risk = publishedOfferRequest()!!
        assertEquals(2_400_000L, risk.valorDispositivo)
        assertEquals("Pixel", risk.marca)
        assertEquals(false, risk.masDe12Meses)
        val offer = bff.offer.quote("Protección de dispositivo", risk).ready()
        assertEquals("COT-1042", offer.cotizacionId)
        assertEquals("Protección de dispositivo", offer.ramo)
        assertEquals("oferta_vigente", offer.estado)
        assertEquals(89_000L, offer.prima)
        assertEquals("COP", offer.moneda)
        assertEquals("2026-10-01", offer.venceEn)
        assertEquals(offer, bff.offer.requote("COT-1042").ready())

        val issued = bff.issuance.accept("COT-1042").ready()
        assertEquals("POL-88219-CO", issued.numero)
        assertEquals("Protección de dispositivo", issued.ramo)
        assertEquals("vigente", issued.estado)
        assertEquals("2027-03-12", issued.venceEn)
        val wallet = bff.issuance.wallet().ready()
        assertEquals(wallet, bff.issuance.wallet().ready())
        val entry = wallet.single()
        assertEquals("POL-88219-CO", entry.numero)
        assertEquals("Protección de dispositivo", entry.ramo)
        assertEquals("Robo, Pantalla, Hurto", entry.resumen)
        assertEquals("vigente", entry.estado)
        assertEquals("2027-03-12", entry.venceEn)
        val detail = bff.issuance.detail("POL-88219-CO").ready()
        assertEquals("POL-88219-CO", detail.numero)
        assertEquals("Protección de dispositivo", detail.ramo)
        assertEquals("Robo y Pantalla", detail.resumen)
        assertEquals("vigente", detail.estado)
        assertEquals("2027-03-12", detail.venceEn)
        assertEquals("Toma la foto del daño y anota fecha y lugar.", detail.queHacer)

        val notice = MockClaimRepository().readNotice()!!
        assertEquals("POL-88219-CO", notice.poliza)
        assertEquals("2026-03-12", notice.fechaHecho)
        assertEquals(4.6533, notice.geo!!.lat, 0.0)
        assertEquals(-74.0836, notice.geo!!.lng, 0.0)
        assertEquals(12, notice.geo!!.precisionM)
        assertEquals(4, notice.adjuntos.size)
        assertEquals(AttachmentKind.FOTO, notice.adjuntos[0].tipo)
        assertEquals("dano.jpg", notice.adjuntos[0].nombre)
        assertEquals(AttachmentKind.VIDEO, notice.adjuntos[1].tipo)
        assertEquals(AttachmentKind.RECIBO, notice.adjuntos[2].tipo)
        assertEquals(AttachmentKind.SOPORTE, notice.adjuntos[3].tipo)
        val receipt = bff.claim.notify(notice).ready()
        assertEquals("SIN-441", receipt.siniestroId)
        assertEquals(ClaimStatus.RECIBIDO, receipt.estado)
        val claim = bff.claim.list().ready().single()
        assertEquals("SIN-441", claim.siniestroId)
        assertEquals("Protección de dispositivo", claim.ramo)
        assertEquals(ClaimStatus.EN_EVALUACION, claim.estado)
        assertEquals("Pantalla rota", claim.resumen)

        val payment = bff.payment.read().ready()
        assertEquals("SIN-220", payment.siniestroId)
        assertEquals("POL-11002-CO", payment.poliza)
        assertEquals("retraso mayor a 120 min", payment.umbral)
        assertEquals(250_000L, payment.monto)
        assertEquals("COP", payment.moneda)
        assertEquals("pagado", payment.estado)

        val profile = publishedMortgageRequest()!!
        assertEquals(180_000_000L, profile.valor)
        assertEquals(180, profile.plazoMeses)
        assertEquals(true, profile.consentimientoPerfil)
        val mortgage = bff.mortgage.offer(profile).ready()
        assertEquals("Vida crediticia", mortgage.ramo)
        assertEquals("oferta_vigente", mortgage.estado)
        assertEquals(64_000L, mortgage.prima)
        assertEquals("COP", mortgage.moneda)
        assertEquals(listOf("plazo", "valor del crédito"), mortgage.factores)
        assertEquals(false, mortgage.degradada)

        val notices = bff.notices.list().ready()
        assertEquals("vencimiento", notices[0].tipo)
        assertEquals("2027-03-12", notices[0].venceEn)
        assertNull(notices[0].estado)
        assertEquals("renovacion", notices[1].tipo)
        assertNull(notices[1].venceEn)
        assertEquals("POL-88219-CO", notices[1].poliza)

        assertEquals("POL-88219-CO", bff.policyCommand.renew("POL-88219-CO").ready().numero)
        assertEquals("POL-88219-CO", bff.policyCommand.modify("POL-88219-CO").ready().numero)
        assertEquals("POL-88219-CO", bff.policyCommand.cancel("POL-88219-CO", "El cliente lo pidió").ready().numero)

        val home = bff.home.load().ready()
        assertEquals("COT-1042", home.ofertaVigente.cotizacionId)
        assertEquals("Protección de dispositivo", home.ofertaVigente.ramo)
        assertEquals("oferta_vigente", home.ofertaVigente.estado)
        assertEquals("POL-88219-CO", home.poliza.numero)
        assertEquals("Protección de dispositivo", home.poliza.ramo)
        assertEquals("vigente", home.poliza.estado)
        assertEquals("SIN-441", home.siniestroEnCurso.siniestroId)
        assertEquals("en_evaluacion", home.siniestroEnCurso.estado)
        assertNull(home.hipotecario)

        val registration = bff.push.register(PushRegistration("fcm-stub", "android")).ready()
        assertEquals("fcm-stub", registration.token)
        assertEquals("android", registration.plataforma)
        val push = bff.push.notice().ready()
        assertEquals(PushType.VENCIMIENTO, push.tipo)
        assertEquals("Tu póliza vence", push.titulo)
        assertEquals("En 7 días", push.cuerpo)
        assertEquals(PushDestination.AVISO_VENCIMIENTO, push.destino)
        assertEquals("POL-88219-CO", push.poliza)

        val providers = bff.assistance.providers().ready()
        assertEquals("PR-1", providers[0].id)
        assertEquals("Taller Norte", providers[0].nombre)
        assertEquals(1.2, providers[0].distanciaKm, 0.0)
        assertEquals("Chapinero", providers[0].zona)
        assertEquals("Kennedy", providers[1].zona)
        val request = publishedAssistanceRequest()!!
        assertEquals("PR-1", request.prestadorId)
        assertEquals(4.6533, request.lat, 0.0)
        assertEquals(-74.0836, request.lng, 0.0)
        assertEquals("POL-88219-CO", request.poliza)
        val assistance = bff.assistance.request(request).ready()
        assertEquals("AS-18", assistance.asistenciaId)
        assertEquals("registrada", assistance.estado)
    }

    @Test
    fun givenPublishedVariants_whenRead_thenTheyStaySuccessful() = runBlocking {
        val rejection = bff.issuance.rejected().ready()
        assertEquals("rechazada", rejection.estado)
        assertEquals("Valor del equipo fuera de rango", rejection.motivo)

        val withoutGeo = MockClaimRepository().readNotice(PublishedSamples.CLAIM_NOTICE_NO_GEO)!!
        assertNull(withoutGeo.geo)
        assertEquals(ClaimStatus.RECIBIDO, bff.claim.notify(withoutGeo).ready().estado)

        assertEquals(true, bff.mortgage.degraded().ready().degradada)
        assertEquals(64_000L, bff.mortgage.degraded().ready().prima)
    }

    @Test
    fun givenABodyOutsideTheContract_whenRead_thenItIsNotASuccess() = runBlocking {
        assertNull(decode<OfferOutDto>("""{"cotizacionId":"COT-1042"}"""))
        val brokenSignup = PublishedSamples.SIGNUP.replace("\"ok\"", "\"maybe\"")
        assertNull(decode<SignupDto>(brokenSignup))
        assertNull(decode<ClaimReceiptDto>("""{"siniestroId":"SIN-441","estado":"otro"}"""))
        assertNull(decode<PolicyCommandDto>("""{"numero":"POL-88219-CO","verbo":"borrar"}"""))
        assertNull(decode<PushNoticeDto>(PublishedSamples.PUSH_NOTICE.replace("vencimiento", "otro")))
        assertNull(
            decode<PushNoticeDto>(
                PublishedSamples.PUSH_NOTICE.replace("aviso-vencimiento", "otro-destino"),
            ),
        )
        assertTrue(bff.policyCommand.cancel("POL-88219-CO", null) is StandInAnswer.Failed)
        assertTrue(bff.policyCommand.cancel("POL-88219-CO", "   ") is StandInAnswer.Failed)
        assertNull(MockClaimRepository().readNotice("{"))
    }

    @Test
    fun givenEveryClosedChoice_whenMapped_thenTheEntityUsesThatChoice() = runBlocking {
        assertEquals("camila@correo.com", decode<SessionInDto>(PublishedSamples.SESSION_IN)!!.correo)
        assertEquals("jwt", decode<RefreshInDto>(PublishedSamples.REFRESH_IN)!!.refreshToken)
        assertEquals("COT-1042", decode<IdDto>(PublishedSamples.REQUOTE_IN)!!.cotizacionId)
        assertEquals("COT-1042", decode<IdDto>(PublishedSamples.ACCEPT_IN)!!.cotizacionId)

        val refused = decode<SignupDto>(PublishedSamples.SIGNUP.replace("\"ok\"", "\"no\""))!!.toRecord()
        assertEquals(Liveness.NO, refused.pruebaDeVida)
        assertNull(RejectionDto("vigente", "otro").toRejection())

        val issued = bff.issuance.accept("COT-1042").ready()
        val modify = decode<PolicyCommandDto>(PublishedSamples.RENEW.replace("renovar", "modificar"))!!
        assertEquals("POL-88219-CO", modify.numero)
        assertEquals(issued, modify.toPolicyOrNull(issued))
        val renew = decode<PolicyCommandDto>(PublishedSamples.RENEW)!!
        assertEquals(issued, renew.toPolicyOrNull(issued))
        assertNull(PolicyCommandDto(issued.numero, PolicyVerbDto.cancelar, "").toPolicyOrNull(issued))

        listOf("decidido", "enrutado", "pagado").forEach { estado ->
            val receipt = decode<ClaimReceiptDto>("""{"siniestroId":"SIN-441","estado":"$estado"}""")!!.toReceipt()
            assertEquals(estado, receipt.estado.name.lowercase())
        }

        listOf(
            "pago_automatico" to "parametrico",
            "renovacion" to "aviso-renovacion",
            "estado_siniestro" to "detalle-siniestro",
        ).forEach { (tipo, destino) ->
            val notice = decode<PushNoticeDto>(
                """{"tipo":"$tipo","titulo":"Aviso","cuerpo":"Cuerpo","destino":"$destino","poliza":"POL-88219-CO"}""",
            )!!.toNotice()
            assertEquals(tipo, notice.tipo.name.lowercase())
            assertEquals(destino, notice.destino.name.lowercase().replace('_', '-'))
        }
    }

    @Test
    fun givenAPublishedBody_whenTheDtoIsBuilt_thenEachFieldIsReadable() = runBlocking {
        val session = SessionInDto("camila@correo.com", "********")
        assertEquals("********", session.contrasena)
        assertEquals("jwt", SessionOutDto("jwt", "jwt", 900).refreshToken)
        assertEquals("jwt", RefreshInDto("jwt").refreshToken)
        val signup = SignupDto("Camila", "Restrepo", "1012345678", "camila@correo.com", LivenessDto.ok, true)
        assertEquals(LivenessDto.no, signup.copy(pruebaDeVida = LivenessDto.no).pruebaDeVida)
        assertEquals(false, RevokeDto(false).habeasData)
        val risk = DeviceRiskDto(2_400_000L, "Pixel", false)
        assertEquals("Protección de dispositivo", OfferInDto("Protección de dispositivo", risk).ramo)
        assertEquals("oferta_vigente", OfferOutDto("COT-1042", "Protección de dispositivo", "oferta_vigente", 89_000L, "COP", "2026-10-01").estado)
        assertEquals("COT-1042", IdDto("COT-1042").cotizacionId)
        assertEquals("vigente", IssuedDto("POL-88219-CO", "Protección de dispositivo", "vigente", "2027-03-12").estado)
        val entry = WalletEntryDto("POL-88219-CO", "Protección de dispositivo", "Robo, Pantalla, Hurto", "vigente", "2027-03-12")
        assertEquals(entry.numero, WalletDto(listOf(entry)).polizas.single().numero)
        assertEquals("Robo y Pantalla", DetailDto("POL-88219-CO", "Protección de dispositivo", "Robo y Pantalla", "vigente", "2027-03-12", "Toma la foto del daño y anota fecha y lugar.").resumen)
        val geo = GeoDto(4.6533, -74.0836, 12)
        assertEquals(12, geo.precisionM)
        val photo = AttachmentDto(AttachmentKindDto.foto, "dano.jpg")
        val withGeo = ClaimNoticeDto("POL-88219-CO", "2026-03-12", geo, listOf(photo))
        val withoutGeo = ClaimNoticeDto("POL-88219-CO", "2026-03-12", adjuntos = listOf(photo))
        assertEquals(geo.lat, withGeo.geo!!.lat, 0.0)
        assertNull(withoutGeo.geo)
        assertEquals(ClaimStatusDto.recibido, ClaimReceiptDto("SIN-441", ClaimStatusDto.recibido).estado)
        val summary = ClaimSummaryDto("SIN-441", "Protección de dispositivo", "Pantalla rota", ClaimStatusDto.en_evaluacion)
        assertEquals(summary.siniestroId, ClaimsDto(listOf(summary)).siniestros.single().siniestroId)
        assertEquals("pagado", PaymentDto("SIN-220", "POL-11002-CO", "retraso mayor a 120 min", 250_000L, "COP", "pagado").estado)
        val credit = CreditDto(180_000_000L, 180)
        assertEquals(true, MortgageInDto(credit, true).consentimientoPerfil)
        assertEquals(false, MortgageOutDto("Vida crediticia", "oferta_vigente", 64_000L, "COP", listOf("plazo"), false).degradada)
        val dated = NoticeDto("vencimiento", "POL-88219-CO", "2027-03-12", "vigente")
        val open = NoticeDto("renovacion", "POL-88219-CO")
        assertEquals("vigente", NoticesDto(listOf(dated, open)).avisos.first().estado)
        assertNull(open.venceEn)
        assertEquals(PolicyVerbDto.renovar, PolicyCommandDto("POL-88219-CO", PolicyVerbDto.renovar).verbo)
        assertEquals("motivo", PolicyCommandDto("POL-88219-CO", PolicyVerbDto.modificar, "motivo").motivo)
        val offerSlot = HomeOfferDto("COT-1042", "Protección de dispositivo", "oferta_vigente")
        val policySlot = HomePolicyDto("POL-88219-CO", "Protección de dispositivo", "vigente")
        val claimSlot = HomeClaimDto("SIN-441", "en_evaluacion")
        assertNull(HomeDto(offerSlot, policySlot, claimSlot).hipotecario)
        assertEquals("vida", HomeDto(offerSlot, policySlot, claimSlot, "vida").hipotecario)
        assertEquals("android", PushRegistrationDto("fcm-stub", "android").plataforma)
        assertEquals(
            PushDestinationDto.`aviso-vencimiento`,
            PushNoticeDto(PushTypeDto.vencimiento, "Tu póliza vence", "En 7 días", PushDestinationDto.`aviso-vencimiento`, "POL-88219-CO").destino,
        )
        val provider = ProviderDto("PR-1", "Taller Norte", 1.2, "Chapinero")
        assertEquals(provider.id, ProvidersDto(listOf(provider)).prestadores.single().id)
        val where = AssistanceGeoDto(4.6533, -74.0836)
        assertEquals("PR-1", AssistanceInDto("PR-1", where, "POL-88219-CO").prestadorId)
        assertEquals("registrada", AssistanceOutDto("AS-18", "registrada").estado)
    }

    @Test
    fun givenClimateWithoutAReference_whenEncoded_thenReferenciaIsOmitted() {
        val blank = ClimateRisk("Retraso de vuelo", "  ", 4).toRequestElement().toString()
        assertFalse(blank.contains("referencia"))
        assertTrue(blank.contains("evento"))
        assertTrue(blank.contains("umbral"))
        val kept = ClimateRisk("lluvia", "BOG", 40).toRequestElement().toString()
        assertTrue(kept.contains("referencia"))
    }

    @Test
    fun givenLivenessNoAndNoGeo_whenMapped_thenThoseChoicesStay() {
        val signup = publishedSignup().copy(pruebaDeVida = Liveness.NO)
        assertEquals(LivenessDto.no, signup.toDto().pruebaDeVida)
        val notice = ClaimNotice("POL-9", "2026-03-12", null, emptyList())
        assertNull(notice.toDto().geo)
    }

    private fun <T> StandInAnswer<T>.ready(): T {
        val ready = this as StandInAnswer.Ready
        return ready.value
    }
}
