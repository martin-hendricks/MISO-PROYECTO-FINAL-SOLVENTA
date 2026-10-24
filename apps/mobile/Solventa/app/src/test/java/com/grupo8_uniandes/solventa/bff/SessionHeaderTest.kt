package com.grupo8_uniandes.solventa.bff

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.bff.fixture.PublishedSamples
import com.grupo8_uniandes.solventa.data.bff.remote.BffCache
import com.grupo8_uniandes.solventa.data.bff.remote.BffClients
import com.grupo8_uniandes.solventa.data.bff.remote.BffGate
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteOfferRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteSessionRepository
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class SessionHeaderTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val server = MockWebServer()
    private lateinit var tokens: TokenStore

    @Before
    fun setUp() {
        server.start()
        tokens = TokenStore(context).also { it.clear() }
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun givenAStoredToken_whenSigningInOrRefreshing_thenNoAuthorizationAndNoRolAreSent() = runBlocking {
        tokens.save(SessionTokens("stale", "stale-refresh", 1))
        val session = session()
        enqueue(PublishedSamples.SESSION_OUT)
        session.signIn("camila@correo.com", "********")
        val signIn = server.takeRequest()
        assertNull(signIn.getHeader("Authorization"))
        assertFalse(signIn.body.readUtf8().contains("rol"))

        enqueue(PublishedSamples.SESSION_OUT)
        session.refresh("jwt")
        val refresh = server.takeRequest()
        assertNull(refresh.getHeader("Authorization"))
        assertFalse(refresh.body.readUtf8().contains("rol"))
        assertEquals("jwt", tokens.read()?.accessToken)
    }

    @Test
    fun givenAProtectedCall_whenTheTokenIsPresent_thenItIsSentAsBearer() = runBlocking {
        tokens.save(SessionTokens("jwt-access", "jwt-refresh", 900))
        enqueue(PublishedSamples.OFFER_OUT)
        val ready = RemoteOfferRepository(api(), gate()).requote("COT-1042") as StandInAnswer.Ready
        assertEquals("COT-1042", ready.value.cotizacionId)
        assertEquals("Bearer jwt-access", server.takeRequest().getHeader("Authorization"))
    }

    @Test
    fun givenAFirst401_whenTheRefreshWorks_thenTheCallIsRetriedOnce() = runBlocking {
        tokens.save(SessionTokens("expired", "refresh-me", 1))
        server.enqueue(MockResponse().setResponseCode(401))
        enqueue(PublishedSamples.SESSION_OUT)
        enqueue(PublishedSamples.OFFER_OUT)
        val answer = RemoteOfferRepository(api(), gate()).requote("COT-1042")
        assertTrue(answer is StandInAnswer.Ready)
        val first = server.takeRequest()
        val refresh = server.takeRequest()
        val retry = server.takeRequest()
        assertTrue(first.path.orEmpty().contains("cotizaciones"))
        assertTrue(refresh.path.orEmpty().contains("sesion/refresh"))
        assertNull(refresh.getHeader("Authorization"))
        assertEquals("Bearer jwt", retry.getHeader("Authorization"))
        assertEquals(0, server.requestCount - 3)
    }

    @Test
    fun givenASecond401_whenRefreshAlsoFails_thenTheLocalSessionIsCleared() = runBlocking {
        tokens.save(SessionTokens("expired", "refresh-me", 1))
        server.enqueue(MockResponse().setResponseCode(401))
        server.enqueue(MockResponse().setResponseCode(401))
        val answer = RemoteOfferRepository(api(), gate()).requote("COT-1042")
        assertTrue(answer is StandInAnswer.Failed)
        assertNull(tokens.read())
    }

    @Test
    fun givenNoToken_whenAProtectedCallIsRejected_thenNothingIsStored() = runBlocking {
        server.enqueue(MockResponse().setResponseCode(401))
        val answer = RemoteOfferRepository(api(), gate()).requote("COT-1042")
        assertTrue(answer is StandInAnswer.Failed)
        assertNull(tokens.read())
    }

    @Test
    fun givenSignInIsRejected_whenTheCallReturns_thenRefreshIsNotAttempted() = runBlocking {
        enqueue(PublishedSamples.SESSION_OUT)
        val signed = session().signIn("camila@correo.com", "********") as StandInAnswer.Ready
        assertEquals("jwt", signed.value.accessToken)
        server.enqueue(MockResponse().setResponseCode(401))
        assertTrue(session().signIn("camila@correo.com", "********") is StandInAnswer.Failed)
        assertEquals(2, server.requestCount)
    }

    @Test
    fun givenRefreshCannotBeReached_whenTheCallIsRejected_thenTheSessionIsCleared() = runBlocking {
        tokens.save(SessionTokens("expired", "refresh-me", 1))
        server.enqueue(MockResponse().setResponseCode(401))
        server.enqueue(MockResponse().setSocketPolicy(okhttp3.mockwebserver.SocketPolicy.NO_RESPONSE))
        val api = BffClients.open(server.url("/").toString(), tokens, readTimeoutSeconds = 1).api
        val answer = RemoteOfferRepository(api, BffGate(api, BffCache(context))).requote("COT-1042")
        assertTrue(answer is StandInAnswer.Failed)
        assertNull(tokens.read())
    }

    @Test
    fun givenSignOutFails_whenTheCallReturns_thenTheLocalSessionIsStillCleared() = runBlocking {
        tokens.save(SessionTokens("jwt-access", "jwt-refresh", 900))
        server.enqueue(MockResponse().setResponseCode(500))
        val answer = session().signOut()
        assertTrue(answer is StandInAnswer.Failed)
        assertNull(tokens.read())
        tokens.save(SessionTokens("jwt-access", "jwt-refresh", 900))
        enqueue(PublishedSamples.SESSION_OUT)
        assertTrue(session().signOut() is StandInAnswer.Ready)
        assertNull(tokens.read())
        tokens.save(SessionTokens("jwt-access", "jwt-refresh", 900))
        val deadApi = BffClients.open("http://127.0.0.1:1", tokens, readTimeoutSeconds = 1).api
        val dead = RemoteSessionRepository(deadApi, tokens, BffGate(deadApi, BffCache(context)))
        assertTrue(dead.signOut() is StandInAnswer.Failed)
        assertNull(tokens.read())
    }

    private fun api() = BffClients.open(server.url("/").toString(), tokens).api

    private fun gate() = BffGate(api(), BffCache(context))

    private fun session() = RemoteSessionRepository(api(), tokens, gate())

    private fun enqueue(body: String) {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(body.trim()),
        )
    }
}
