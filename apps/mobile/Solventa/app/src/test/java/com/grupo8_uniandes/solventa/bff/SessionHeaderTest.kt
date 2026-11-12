package com.grupo8_uniandes.solventa.bff

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.bff.fixture.PublishedSamples
import com.grupo8_uniandes.solventa.data.bff.remote.BffCache
import com.grupo8_uniandes.solventa.data.bff.remote.BffClients
import com.grupo8_uniandes.solventa.data.bff.remote.SessionUnauthorized
import com.grupo8_uniandes.solventa.data.bff.remote.BffGate
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteOfferRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteSessionRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteSignupRepository
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRecord
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread
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
        AndroidKeyStoreProvider.install()
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
        assertTrue(signIn.path.orEmpty().contains("sesion/ingreso"))
        assertNull(signIn.getHeader("Authorization"))
        assertFalse(signIn.body.readUtf8().contains("rol"))
        assertEquals(0, server.requestCount - 1)

        enqueue(PublishedSamples.SESSION_OUT)
        session.refresh("jwt")
        val refresh = server.takeRequest()
        assertNull(refresh.getHeader("Authorization"))
        assertFalse(refresh.body.readUtf8().contains("rol"))
        assertEquals("jwt", tokens.read()?.accessToken)
    }

    @Test
    fun givenAStoredToken_whenRegistering_thenNoAuthorizationIsSentAndA401DoesNotRefresh() = runBlocking {
        tokens.save(SessionTokens("stale", "stale-refresh", 1))
        val signup = RemoteSignupRepository(api(), gate())
        enqueue(PublishedSamples.SIGNUP)
        signup.register(signupRecord())
        val created = server.takeRequest()
        assertTrue(created.path.orEmpty().endsWith("/registro"))
        assertNull(created.getHeader("Authorization"))
        val body = created.body.readUtf8()
        assertTrue(body.contains("secreto12"))
        assertTrue(body.contains("\"tipoDocumento\":\"CC\""))

        server.enqueue(MockResponse().setResponseCode(401))
        signup.register(signupRecord())
        server.takeRequest()
        assertEquals(2, server.requestCount)
        assertEquals("stale", tokens.read()?.accessToken)
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
    fun givenACustomer401_whenTheCallReturns_thenLogoutIsNotified() = runBlocking {
        var notified = 0
        SessionUnauthorized.onUnauthorized = { notified += 1 }
        try {
            tokens.save(SessionTokens("expired", "refresh-me", 1))
            server.enqueue(MockResponse().setResponseCode(401))
            server.enqueue(MockResponse().setResponseCode(401))
            val answer = RemoteOfferRepository(api(), gate()).requote("COT-1042")
            assertTrue(answer is StandInAnswer.Failed)
            assertEquals(1, notified)
            assertNull(tokens.read())
        } finally {
            SessionUnauthorized.onUnauthorized = null
        }
    }

    @Test
    fun givenSignOutIsUnauthorized_whenTheCallReturns_thenLogoutIsNotNotified() = runBlocking {
        var notified = 0
        SessionUnauthorized.onUnauthorized = { notified += 1 }
        try {
            tokens.save(SessionTokens("expired", "refresh-me", 1))
            server.enqueue(MockResponse().setResponseCode(401))
            server.enqueue(MockResponse().setResponseCode(401))
            assertTrue(session().signOut() is StandInAnswer.Failed)
            assertEquals(0, notified)
            assertNull(tokens.read())
        } finally {
            SessionUnauthorized.onUnauthorized = null
        }
    }

    @Test
    fun givenSignInIsUnauthorized_whenTheCallReturns_thenLogoutIsNotNotified() = runBlocking {
        var notified = 0
        SessionUnauthorized.onUnauthorized = { notified += 1 }
        try {
            server.enqueue(MockResponse().setResponseCode(401))
            assertTrue(session().signIn("camila@correo.com", "secret") is StandInAnswer.Failed)
            assertEquals(0, notified)
        } finally {
            SessionUnauthorized.onUnauthorized = null
        }
    }

    @Test
    fun givenNoToken_whenAProtectedCallIsRejected_thenNothingIsStored() = runBlocking {
        val before = server.requestCount
        val answer = RemoteOfferRepository(api(), gate()).requote("COT-1042")
        assertTrue(answer is StandInAnswer.Failed)
        assertEquals(before, server.requestCount)
        assertNull(tokens.read())
    }

    @Test
    fun givenAForbiddenCredential_whenAProtectedCallIsRefused_thenTheBodyIsAbsentAndTheCredentialRemains() = runBlocking {
        tokens.save(SessionTokens("jwt-access", "jwt-refresh", 900))
        server.enqueue(
            MockResponse()
                .setResponseCode(403)
                .setBody(PublishedSamples.OFFER_OUT.trim()),
        )
        val answer = RemoteOfferRepository(api(), gate()).requote("COT-1042")
        assertTrue(answer is StandInAnswer.Failed)
        assertFalse(answer is StandInAnswer.Ready<*>)
        assertEquals("jwt-access", tokens.read()?.accessToken)
        assertEquals("jwt-refresh", tokens.read()?.refreshToken)
        assertEquals(900, tokens.read()?.expiraEn)
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

    @Test
    fun givenTwoRequestsLoseTheirAccessToken_whenTheyRefresh_thenOnlyOneRotationHappens() {
        tokens.save(SessionTokens("expired", "refresh-me", 1))
        val refreshes = AtomicInteger(0)
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                val path = request.path.orEmpty()
                if (path.contains("sesion/refresh")) {
                    refreshes.incrementAndGet()
                    Thread.sleep(150)
                    return json(
                        """{"accessToken":"rotated","refreshToken":"rotated-refresh","expiraEn":900}""",
                    )
                }
                val authorization = request.getHeader("Authorization")
                if (authorization == "Bearer rotated") return json(PublishedSamples.OFFER_OUT)
                if (authorization == "Bearer expired") return MockResponse().setResponseCode(401)
                return MockResponse().setResponseCode(500)
            }
        }
        val repository = RemoteOfferRepository(api(), gate())
        val start = CountDownLatch(1)
        val done = CountDownLatch(2)
        val failures = AtomicInteger(0)
        repeat(2) {
            thread {
                start.await()
                val answer = runBlocking { repository.requote("COT-1042") }
                if (answer !is StandInAnswer.Ready) failures.incrementAndGet()
                done.countDown()
            }
        }
        start.countDown()
        assertTrue(done.await(10, TimeUnit.SECONDS))
        assertEquals(0, failures.get())
        assertEquals(1, refreshes.get())
        assertEquals("rotated", tokens.read()?.accessToken)
    }

    @Test
    fun givenEncryptedReadFails_whenRead_thenTheStoreRecoversEmpty() {
        val broken = java.lang.reflect.Proxy.newProxyInstance(
            android.content.SharedPreferences::class.java.classLoader,
            arrayOf(android.content.SharedPreferences::class.java),
        ) { _, method, _ ->
            if (method.name == "getString" || method.name == "edit") throw SecurityException("corrupt")
            null
        } as android.content.SharedPreferences
        val field = TokenStore::class.java.getDeclaredField("prefs")
        field.isAccessible = true
        field.set(tokens, broken)
        assertNull(tokens.read())
        tokens.save(SessionTokens("fresh", "fresh-refresh", 30))
        assertEquals("fresh", tokens.read()?.accessToken)
    }

    @Test
    fun givenABlankToken_whenRead_thenTheSessionIsAbsent() {
        tokens.save(SessionTokens(" ", "refresh", 1))
        assertNull(tokens.read())
        tokens.save(SessionTokens("access", "", 1))
        assertNull(tokens.read())
        tokens.save(SessionTokens("access", " ", 1))
        assertNull(tokens.read())
        tokens.clear()
        assertNull(tokens.read())
    }

    @Test
    fun givenASavedCredential_whenReadAsPlainPreferences_thenTheAccessTokenIsNotVisible() {
        tokens.save(SessionTokens("jwt-access", "jwt-refresh", 900))
        val plain = context.getSharedPreferences("solventa.tokens", Context.MODE_PRIVATE)
        val visible = plain.all.entries.joinToString { "${it.key}=${it.value}" }
        assertFalse(visible.contains("jwt-access"))
        assertFalse(visible.contains("jwt-refresh"))
        val stored = tokens.read()
        assertEquals("jwt-access", stored?.accessToken)
        assertEquals("jwt-refresh", stored?.refreshToken)
        assertEquals(900, stored?.expiraEn)
    }

    private fun api() = BffClients.open(server.url("/").toString(), tokens).api

    private fun gate() = BffGate(api(), BffCache(context))

    private fun session() = RemoteSessionRepository(api(), tokens, gate())

    private fun signupRecord() = SignupRecord(
        "Camila",
        "Restrepo",
        "1012345678",
        "camila@correo.com",
        Liveness.NO,
        false,
        contrasena = "secreto12",
        tipoDocumento = "CC",
    )

    private fun json(body: String) = MockResponse()
        .setResponseCode(200)
        .setHeader("Content-Type", "application/json")
        .setBody(body.trim())

    private fun enqueue(body: String) {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(body.trim()),
        )
    }
}
