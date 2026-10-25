package com.grupo8_uniandes.solventa.bff

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.bff.fixture.PublishedSamples
import com.grupo8_uniandes.solventa.data.bff.remote.BffCache
import com.grupo8_uniandes.solventa.data.bff.remote.MobileBffApi
import com.grupo8_uniandes.solventa.data.bff.remote.BffClients
import com.grupo8_uniandes.solventa.data.bff.remote.BffGate
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteAssistanceRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteClaimRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteHomeBffRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteIssuanceRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteMortgageRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteNoticeRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteOfferRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemotePaymentRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemotePolicyCommandRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemotePushRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteSignupRepository
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.mortgage.CreditProfile
import com.grupo8_uniandes.solventa.domain.bff.offer.ClimateRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.DeviceRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.LifeRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.MortgageRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.PaymentsRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.TravelRisk
import com.grupo8_uniandes.solventa.domain.bff.push.PushRegistration
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRecord
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.SocketPolicy
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class BffCallTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val server = MockWebServer()
    private lateinit var tokens: TokenStore
    private lateinit var cache: BffCache
    private lateinit var gate: BffGate

    @Before
    fun setUp() {
        server.start()
        tokens = TokenStore(context).also { it.clear() }
        cache = BffCache(context).also { it.clear() }
        val api = BffClients.open(server.url("/").toString(), tokens).api
        gate = BffGate(api, cache)
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun givenAReadableBody_whenTheHostAnswers_thenDegradedAndEmptyOriginationStayReady() = runBlocking {
        enqueue(PublishedSamples.MORTGAGE_DEGRADED)
        val mortgage = RemoteMortgageRepository(api(), gate).offer(CreditProfile(180_000_000, 180, true))
        val ready = mortgage as StandInAnswer.Ready
        assertTrue(ready.value.degradada)
        assertEquals(64_000L, ready.value.prima)

        enqueue(PublishedSamples.HOME)
        val home = RemoteHomeBffRepository(api(), gate).load() as StandInAnswer.Ready
        assertNull(home.value.hipotecario)
        assertEquals("COT-1042", home.value.ofertaVigente.cotizacionId)
    }

    @Test
    fun givenAClosedFailure_whenAsked_thenThePublishedPremiumIsAbsent() = runBlocking {
        val offer = RemoteOfferRepository(api(), gate)
        listOf(403, 404, 409, 422, 503).forEach { code ->
            server.enqueue(MockResponse().setResponseCode(code).setBody("""{"codigo":"x","mensaje":"no"}"""))
            assertTrue(offer.requote("COT-1042") is StandInAnswer.Failed)
        }
        server.enqueue(MockResponse().setResponseCode(200).setBody("{"))
        assertTrue(offer.requote("COT-1042") is StandInAnswer.Failed)
    }

    @Test
    fun givenASilentHost_whenAsked_thenTheAskFails() = runBlocking {
        server.enqueue(MockResponse().setSocketPolicy(SocketPolicy.NO_RESPONSE))
        val api = BffClients.open(server.url("/").toString(), tokens, readTimeoutSeconds = 1).api
        val answer = RemoteOfferRepository(api, BffGate(api, cache)).requote("COT-1042")
        assertTrue(answer is StandInAnswer.Failed)
    }

    @Test
    fun givenEachLine_whenQuoted_thenDatosRiesgoMatchesThatLine() = runBlocking {
        val offer = RemoteOfferRepository(api(), gate)
        val cases = listOf(
            "valorDispositivo" to DeviceRisk(2_400_000, "Pixel", false),
            "sumaAsegurada" to LifeRisk(50_000_000, 34),
            "evento" to ClimateRisk("lluvia", "Chapinero", 40),
            "\"valor\"" to MortgageRisk(180_000_000, 180),
            "cuota" to PaymentsRisk(900_000, 12),
            "destino" to TravelRisk("Bogotá", 7),
        )
        cases.forEach { (field, risk) ->
            enqueue(PublishedSamples.OFFER_OUT)
            val answer = offer.quote("linea", risk) as StandInAnswer.Ready
            assertEquals("COT-1042", answer.value.cotizacionId)
            val recorded = server.takeRequest()
            val body = recorded.body.readUtf8()
            assertTrue(body.contains(field))
            val key = recorded.getHeader("Idempotency-Key").orEmpty()
            assertTrue(key.length in 8..128)
            assertFalse(body.contains("\"rol\""))
        }
        enqueue(PublishedSamples.OFFER_OUT)
        enqueue(PublishedSamples.OFFER_OUT)
        offer.requote("COT-1042")
        offer.requote("COT-1042")
        val left = server.takeRequest().getHeader("X-Correlation-Id")
        val right = server.takeRequest().getHeader("X-Correlation-Id")
        assertNotEquals(left, right)
    }

    @Test
    fun givenNoStoredWallet_whenTheHostIsUnreachable_thenTheLoadFails() = runBlocking {
        val dead = deadClients()
        assertTrue(RemoteIssuanceRepository(dead.api, dead.gate, cache).wallet() is StandInAnswer.Failed)

        enqueue(PublishedSamples.WALLET)
        val stored = RemoteIssuanceRepository(api(), gate, cache).wallet() as StandInAnswer.Ready
        assertEquals("POL-88219-CO", stored.value.single().numero)

        assertTrue(RemoteIssuanceRepository(dead.api, dead.gate, cache).wallet() is StandInAnswer.Failed)

        server.enqueue(MockResponse().setResponseCode(503).setBody("""{"codigo":"x","mensaje":"no"}"""))
        assertTrue(RemoteIssuanceRepository(api(), gate, cache).wallet() is StandInAnswer.Failed)
    }

    @Test
    fun givenAClaimThatCannotLeave_whenALaterAskConnects_thenTheSameKeyIsSentOnce() = runBlocking {
        val dead = deadClients()
        val notice = ClaimNotice(
            poliza = "POL-88219-CO",
            fechaHecho = "2026-03-12",
            geo = null,
            adjuntos = listOf(
                Attachment(AttachmentKind.FOTO, "dano.jpg"),
                Attachment(AttachmentKind.VIDEO, "dano.mp4"),
                Attachment(AttachmentKind.RECIBO, "recibo.jpg"),
                Attachment(AttachmentKind.SOPORTE, "acta.jpg"),
            ),
        )
        assertTrue(RemoteClaimRepository(dead.api, dead.gate, cache).notify(notice) is StandInAnswer.Failed)
        val key = cache.readClaim()!!.key

        enqueue(PublishedSamples.CLAIM_RECEIPT)
        enqueue(PublishedSamples.CLAIM_RECEIPT)
        val sent = RemoteClaimRepository(api(), gate, cache).notify(notice.copy(fechaHecho = "2026-03-13")) as StandInAnswer.Ready
        assertEquals("SIN-441", sent.value.siniestroId)
        val replay = server.takeRequest()
        val fresh = server.takeRequest()
        assertEquals(key, replay.getHeader("Idempotency-Key"))
        assertNotEquals(key, fresh.getHeader("Idempotency-Key"))
        val replayBody = replay.body.readUtf8()
        val freshBody = fresh.body.readUtf8()
        assertTrue(replayBody, replayBody.contains("\"geo\":null"))
        assertTrue(freshBody, freshBody.contains("2026-03-13"))
        assertFalse(replayBody.contains("lat"))
        assertNull(cache.readClaim())
    }

    @Test
    fun givenARejectionBody_whenAcceptanceIsRead_thenItIsNotATransportFailure() = runBlocking {
        enqueue(PublishedSamples.REJECTION)
        val rejection = RemoteIssuanceRepository(api(), gate, cache).rejected() as StandInAnswer.Ready
        assertEquals("rechazada", rejection.value.estado)
        assertEquals("Valor del equipo fuera de rango", rejection.value.motivo)

        enqueue(PublishedSamples.ISSUED)
        val issued = RemoteIssuanceRepository(api(), gate, cache).accept("COT-1042") as StandInAnswer.Ready
        assertEquals("POL-88219-CO", issued.value.numero)

        enqueue(PublishedSamples.REJECTION)
        assertTrue(RemoteIssuanceRepository(api(), gate, cache).accept("COT-1042") is StandInAnswer.Failed)
        enqueue(PublishedSamples.ISSUED)
        assertTrue(RemoteIssuanceRepository(api(), gate, cache).rejected() is StandInAnswer.Failed)
        server.enqueue(MockResponse().setResponseCode(503).setBody("""{"codigo":"x","mensaje":"no"}"""))
        assertTrue(RemoteIssuanceRepository(api(), gate, cache).accept("COT-1042") is StandInAnswer.Failed)
        server.enqueue(MockResponse().setResponseCode(200).setBody("{"))
        assertTrue(RemoteIssuanceRepository(api(), gate, cache).wallet() is StandInAnswer.Failed)
        val dead = deadClients()
        assertTrue(RemoteIssuanceRepository(dead.api, dead.gate, cache).accept("COT-1042") is StandInAnswer.Failed)
    }

    @Test
    fun givenAClaimTheHostRefuses_whenNotified_thenNothingIsQueued() = runBlocking {
        val claims = RemoteClaimRepository(api(), gate, cache)
        val notice = ClaimNotice("POL-88219-CO", "2026-03-12", null, emptyList())
        server.enqueue(MockResponse().setResponseCode(422).setBody("""{"codigo":"x","mensaje":"no"}"""))
        assertTrue(claims.notify(notice) is StandInAnswer.Failed)
        assertNull(cache.readClaim())
        server.enqueue(MockResponse().setResponseCode(200).setBody("{"))
        assertTrue(claims.notify(notice) is StandInAnswer.Failed)

        val dead = deadClients()
        assertTrue(RemoteClaimRepository(dead.api, dead.gate, cache).notify(notice) is StandInAnswer.Failed)
        server.enqueue(MockResponse().setResponseCode(422).setBody("""{"codigo":"x","mensaje":"no"}"""))
        enqueue(PublishedSamples.CLAIM_RECEIPT)
        val sent = RemoteClaimRepository(api(), gate, cache).notify(notice.copy(fechaHecho = "2026-03-14"))
        assertTrue(sent is StandInAnswer.Ready)
        assertNull(cache.readClaim())
    }

    @Test
    fun givenACorruptCache_whenRead_thenItIsAbsent() {
        val prefs = context.getSharedPreferences("solventa.bff", android.content.Context.MODE_PRIVATE)
        prefs.edit().putString("wallet", "{").putString("claim", "{").commit()
        assertNull(cache.readWallet())
        assertNull(cache.readClaim())
    }

    @Test
    fun givenThePublishedAreas_whenEachIsAsked_thenTheSampleIsReady() = runBlocking {
        val signup = RemoteSignupRepository(api(), gate)
        enqueue(PublishedSamples.SIGNUP)
        val record = signup.register(
            SignupRecord("Camila", "Restrepo", "1012345678", "camila@correo.com", Liveness.OK, true),
        ) as StandInAnswer.Ready
        assertEquals(Liveness.OK, record.value.pruebaDeVida)

        enqueue(PublishedSamples.REVOKE)
        assertTrue(signup.revokeConsent() is StandInAnswer.Ready)

        enqueue(PublishedSamples.DETAIL)
        val detail = RemoteIssuanceRepository(api(), gate, cache).detail("POL-88219-CO") as StandInAnswer.Ready
        assertEquals("POL-88219-CO", detail.value.numero)

        enqueue(PublishedSamples.CLAIMS)
        val claims = RemoteClaimRepository(api(), gate, cache).list() as StandInAnswer.Ready
        assertEquals("SIN-441", claims.value.single().siniestroId)

        enqueue(PublishedSamples.PAYMENT)
        val payment = RemotePaymentRepository(api(), gate).read() as StandInAnswer.Ready
        assertEquals(250_000L, payment.value.monto)

        enqueue(PublishedSamples.MORTGAGE_DEGRADED)
        val degraded = RemoteMortgageRepository(api(), gate).degraded() as StandInAnswer.Ready
        assertTrue(degraded.value.degradada)

        enqueue(PublishedSamples.NOTICES)
        assertTrue(RemoteNoticeRepository(api(), gate).list() is StandInAnswer.Ready)

        enqueue(PublishedSamples.ISSUED)
        val renewed = RemotePolicyCommandRepository(api(), gate).renew("POL-88219-CO") as StandInAnswer.Ready
        assertEquals("vigente", renewed.value.estado)

        enqueue(PublishedSamples.ISSUED)
        RemotePolicyCommandRepository(api(), gate).modify("POL-88219-CO")
        enqueue(PublishedSamples.ISSUED)
        RemotePolicyCommandRepository(api(), gate).cancel("POL-88219-CO", "El cliente lo pidió")
        val cancel = generateSequence { server.takeRequest(0, java.util.concurrent.TimeUnit.MILLISECONDS) }
            .first { it.path.orEmpty().contains("ciclo") && it.body.peek().readUtf8().contains("cancelar") }
        assertTrue(cancel.getHeader("Idempotency-Key").orEmpty().length in 8..128)

        enqueue(PublishedSamples.PUSH_REGISTRATION)
        val push = RemotePushRepository(api(), gate)
        assertTrue(push.register(PushRegistration("fcm-stub", "android")) is StandInAnswer.Ready)
        enqueue(PublishedSamples.PUSH_NOTICE)
        val notice = push.notice() as StandInAnswer.Ready
        assertEquals("Tu póliza vence", notice.value.titulo)

        enqueue(PublishedSamples.PROVIDERS)
        val assistance = RemoteAssistanceRepository(api(), gate)
        assertEquals(2, (assistance.providers() as StandInAnswer.Ready).value.size)
        enqueue(PublishedSamples.ASSISTANCE_OUT)
        val requested = assistance.request(AssistanceRequest("PR-1", 4.65, -74.08, "POL-88219-CO"))
        assertTrue(requested is StandInAnswer.Ready)
    }

    private fun api() = BffClients.open(server.url("/").toString(), tokens).api

    private fun deadClients(): Dead {
        val api = BffClients.open("http://127.0.0.1:1", tokens, readTimeoutSeconds = 1).api
        return Dead(api, BffGate(api, cache))
    }

    private class Dead(val api: MobileBffApi, val gate: BffGate)

    private fun enqueue(body: String) {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(body.trim()),
        )
    }
}
