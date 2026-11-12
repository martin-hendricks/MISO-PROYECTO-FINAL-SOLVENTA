package com.grupo8_uniandes.solventa.bff

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.bff.remote.BffClients
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteLivenessRepository
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.domain.bff.signup.LivenessCheck
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import java.net.SocketException

@RunWith(RobolectricTestRunner::class)
class RemoteLivenessRepositoryTest {
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
    fun givenAValidPhoto_whenChecked_thenOkWithoutATokenAndWithACorrelationId() = runBlocking {
        server.enqueue(MockResponse().setBody("""{"resultado":"ok"}"""))
        val answer = repository().check(byteArrayOf(1, 2, 3))
        val request = server.takeRequest()
        assertEquals(LivenessCheck.Passed, answer)
        assertTrue(request.path.orEmpty().endsWith("identidad/prueba-de-vida"))
        assertNull(request.getHeader("Authorization"))
        assertTrue(request.getHeader("X-Correlation-Id").orEmpty().isNotBlank())
        val body = request.body.readUtf8()
        assertTrue(body.contains("name=\"foto\""))
        assertTrue(body.contains("image/jpeg"))
    }

    @Test
    fun givenANoAnswer_whenChecked_thenFailed() = runBlocking {
        server.enqueue(MockResponse().setBody("""{"resultado":"no"}"""))
        assertEquals(LivenessCheck.Failed, repository().check(byteArrayOf(1)))
    }

    @Test
    fun givenA503_whenChecked_thenUnavailable() = runBlocking {
        server.enqueue(MockResponse().setResponseCode(503).setBody("""{"detail":"servicio_no_disponible"}"""))
        assertEquals(LivenessCheck.Unavailable, repository().check(byteArrayOf(1)))
    }

    @Test
    fun givenADroppedConnection_whenChecked_thenUnavailable() = runBlocking {
        server.enqueue(MockResponse().setSocketPolicy(okhttp3.mockwebserver.SocketPolicy.DISCONNECT_AT_START))
        assertEquals(LivenessCheck.Unavailable, repository().check(byteArrayOf(1)))
    }

    @Test
    fun givenAClientError_whenChecked_thenFailed() = runBlocking {
        server.enqueue(MockResponse().setResponseCode(422).setBody("""{"detail":"falta"}"""))
        assertEquals(LivenessCheck.Failed, repository().check(byteArrayOf(1)))
    }

    @Test
    fun givenAStoredToken_whenRecording_thenTheBearerIsSent() = runBlocking {
        tokens.save(SessionTokens("access-token", "refresh-token", 30))
        server.enqueue(MockResponse().setBody("""{"pruebaDeVida":"ok"}"""))
        val answer = repository().record(Liveness.OK)
        val request = server.takeRequest()
        assertTrue(answer is StandInAnswer.Ready)
        assertEquals("Bearer access-token", request.getHeader("Authorization"))
        assertTrue(request.path.orEmpty().endsWith("cliente/prueba-de-vida"))
        assertTrue(request.body.readUtf8().contains("\"pruebaDeVida\":\"ok\""))
    }

    @Test
    fun givenAStoredNo_whenRecording_thenTheAnswerIsNo() = runBlocking {
        tokens.save(SessionTokens("access-token", "refresh-token", 30))
        server.enqueue(MockResponse().setBody("""{"pruebaDeVida":"no"}"""))
        val answer = repository().record(Liveness.NO)
        assertTrue(answer is StandInAnswer.Ready)
        assertEquals(Liveness.NO, (answer as StandInAnswer.Ready).value)
    }

    @Test
    fun givenAServerError_whenRecording_thenFailed() = runBlocking {
        tokens.save(SessionTokens("access-token", "refresh-token", 30))
        server.enqueue(MockResponse().setResponseCode(500))
        assertTrue(repository().record(Liveness.OK) is StandInAnswer.Failed)
    }

    @Test
    fun givenADroppedConnection_whenRecording_thenFailed() = runBlocking {
        tokens.save(SessionTokens("access-token", "refresh-token", 30))
        server.enqueue(MockResponse().setSocketPolicy(okhttp3.mockwebserver.SocketPolicy.DISCONNECT_AT_START))
        assertTrue(repository().record(Liveness.OK) is StandInAnswer.Failed)
    }

    private fun repository() = RemoteLivenessRepository(BffClients.open(server.url("/").toString(), tokens).api)
}
