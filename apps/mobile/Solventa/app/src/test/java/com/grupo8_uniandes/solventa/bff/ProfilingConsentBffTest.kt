package com.grupo8_uniandes.solventa.bff

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.bff.mock.MockProfilingConsentRepository
import com.grupo8_uniandes.solventa.data.bff.mock.StandInControl
import com.grupo8_uniandes.solventa.data.bff.mock.StandInMode
import com.grupo8_uniandes.solventa.data.bff.remote.BffCache
import com.grupo8_uniandes.solventa.data.bff.remote.BffClients
import com.grupo8_uniandes.solventa.data.bff.remote.BffGate
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteProfilingConsentRepository
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ProfilingConsent
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class ProfilingConsentBffTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val server = MockWebServer()
    private lateinit var repository: RemoteProfilingConsentRepository

    @Before
    fun setUp() {
        AndroidKeyStoreProvider.install()
        server.start()
        val tokens = TokenStore(context).also { it.clear() }
        tokens.save(SessionTokens("jwt-access", "jwt-refresh", 900))
        val cache = BffCache(context).also { it.clear() }
        val api = BffClients.open(server.url("/").toString(), tokens).api
        repository = RemoteProfilingConsentRepository(api, BffGate(api, cache))
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun givenAConsentInForce_whenRead_thenItIsGrantedWithItsDate() = runBlocking {
        enqueue(200, """{"estado":"vigente","otorgadoEn":"2026-10-01T10:00:00Z"}""")

        val answer = repository.read()

        assertEquals(StandInAnswer.Ready(ProfilingConsent.Granted("2026-10-01T10:00:00Z")), answer)
        val recorded = server.takeRequest()
        assertEquals("GET", recorded.method)
        assertEquals("/cliente/consentimiento-perfil", recorded.path)
    }

    @Test
    fun givenNoConsent_whenRead_thenItIsNone() = runBlocking {
        enqueue(200, """{"estado":"sin_consentimiento"}""")

        assertEquals(StandInAnswer.Ready(ProfilingConsent.None), repository.read())
    }

    @Test
    fun givenAConsentInForce_whenRevoked_thenTheBffGetsADeleteAndReturnsTheRevocationDate() = runBlocking {
        enqueue(200, """{"estado":"revocado","revocadoEn":"2026-11-11T15:30:00Z"}""")

        val answer = repository.revoke()

        assertEquals(StandInAnswer.Ready(ProfilingConsent.Revoked("2026-11-11T15:30:00Z")), answer)
        val recorded = server.takeRequest()
        assertEquals("DELETE", recorded.method)
        assertEquals("/cliente/consentimiento-perfil", recorded.path)
    }

    @Test
    fun givenTheBffIsDown_whenReadOrRevoked_thenBothFail() = runBlocking {
        enqueue(503, """{"detail":"ms-perfilamiento no disponible"}""")
        enqueue(503, """{"detail":"ms-perfilamiento no disponible"}""")

        assertEquals(StandInAnswer.Failed, repository.read())
        assertEquals(StandInAnswer.Failed, repository.revoke())
    }

    @Test
    fun givenAnUnknownStateOrAMissingDate_whenRead_thenItFails() = runBlocking {
        enqueue(200, """{"estado":"pendiente"}""")
        enqueue(200, """{"estado":"vigente"}""")

        assertEquals(StandInAnswer.Failed, repository.read())
        assertEquals(StandInAnswer.Failed, repository.read())
    }

    @Test
    fun givenTheStandIn_whenRevoked_thenLaterReadsSeeTheRevocation() = runBlocking {
        val standIn = MockProfilingConsentRepository()

        assertEquals(StandInAnswer.Ready(ProfilingConsent.Granted("2026-10-01T10:00:00Z")), standIn.read())
        assertEquals(StandInAnswer.Ready(ProfilingConsent.Revoked("2026-11-11T15:30:00Z")), standIn.revoke())
        assertEquals(StandInAnswer.Ready(ProfilingConsent.Revoked("2026-11-11T15:30:00Z")), standIn.read())
    }

    @Test
    fun givenAFailingStandIn_whenRead_thenItFails() = runBlocking {
        val standIn = MockProfilingConsentRepository(StandInControl(StandInMode.Failure))

        assertEquals(StandInAnswer.Failed, standIn.read())
        assertEquals(StandInAnswer.Failed, standIn.revoke())
    }

    private fun enqueue(code: Int, body: String) {
        server.enqueue(
            MockResponse()
                .setResponseCode(code)
                .setHeader("Content-Type", "application/json")
                .setBody(body),
        )
    }
}
