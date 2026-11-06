package com.grupo8_uniandes.solventa.policy

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.bff.AndroidKeyStoreProvider
import com.grupo8_uniandes.solventa.data.bff.remote.BffCache
import com.grupo8_uniandes.solventa.data.bff.remote.BffClients
import com.grupo8_uniandes.solventa.data.bff.remote.BffGate
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteRenewalPreferenceRepository
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.grupo8_uniandes.solventa.domain.bff.policy.RenewalPreferenceRepository
import com.grupo8_uniandes.solventa.domain.bff.policy.RenewalSave
import com.grupo8_uniandes.solventa.domain.bff.policy.SaveRenewalPreference
import com.grupo8_uniandes.solventa.domain.bff.policy.StandInRenewalPreferenceRepository
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
class RenewalPreferenceTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val server = MockWebServer()
    private lateinit var repository: RemoteRenewalPreferenceRepository

    @Before
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        AndroidKeyStoreProvider.install()
        server.start()
        val tokens = TokenStore(context).also { it.clear() }
        tokens.save(SessionTokens("jwt-access", "jwt-refresh", 900))
        val cache = BffCache(context).also { it.clear() }
        val api = BffClients.open(server.url("/").toString(), tokens).api
        repository = RemoteRenewalPreferenceRepository(api, BffGate(api, cache))
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
        server.shutdown()
    }

    @Test
    fun givenTheIssuedPolicy_whenTheChoiceIsSavedTwice_thenPreferenciasIsCalledAndCicloIsNot() = runBlocking {
        server.enqueue(saved("POL-88219-CO", true))
        val firstSave = repository.save("POL-88219-CO", true)
        val first = server.takeRequest()
        assertTrue(first.path.orEmpty().endsWith("cliente/polizas/POL-88219-CO/preferencias"))
        assertFalse(first.path.orEmpty().contains("ciclo"))
        assertEquals("PATCH", first.method)
        assertTrue(first.body.readUtf8().contains("\"renovacionAutomatica\":true"))
        assertEquals(RenewalSave.Saved(true), firstSave)
        server.enqueue(saved("POL-88219-CO", true))
        val secondSave = repository.save("POL-88219-CO", true)
        val second = server.takeRequest()
        assertTrue(second.path.orEmpty().endsWith("preferencias"))
        assertFalse(second.path.orEmpty().contains("ciclo"))
        assertEquals(RenewalSave.Saved(true), secondSave)
    }

    @Test
    fun givenAnotherCustomersPolicy_whenTheChoiceIsSet_thenNoExisteLeavesTheBoxUnchanged() = runBlocking {
        server.enqueue(MockResponse().setResponseCode(404).setBody("""{"detail":"No existe"}"""))
        val saved = repository.save("POL-OTHER", true)
        assertEquals(RenewalSave.Missing, saved)
        val recorded = server.takeRequest()
        assertFalse(recorded.path.orEmpty().contains("ciclo"))
        val choice = RenewalChoiceViewModel("POL-OTHER", SaveRenewalPreference(object : RenewalPreferenceRepository {
            override suspend fun save(numero: String, enabled: Boolean): RenewalSave = RenewalSave.Missing
        }))
        assertFalse(choice.state.value.checked)
        choice.onChecked(true)
        assertFalse(choice.state.value.checked)
        assertTrue(choice.state.value.missing)
        val failed = RenewalChoiceViewModel("POL-88219-CO", SaveRenewalPreference(object : RenewalPreferenceRepository {
            override suspend fun save(numero: String, enabled: Boolean): RenewalSave = RenewalSave.Failed
        }))
        failed.onChecked(true)
        assertFalse(failed.state.value.checked)
        assertFalse(failed.state.value.missing)
    }

    @Test
    fun givenTheParametricPolicy_whenTheChoiceIsSaved_thenTheDepositIsNotAPremiumCharge() = runBlocking {
        val calls = mutableListOf<String>()
        val local = object : RenewalPreferenceRepository {
            override suspend fun save(numero: String, enabled: Boolean): RenewalSave {
                calls += numero
                return RenewalSave.Saved(enabled)
            }
        }
        val choice = RenewalChoiceViewModel("POL-77310", SaveRenewalPreference(local))
        choice.onChecked(true)
        choice.onChecked(true)
        assertEquals(listOf("POL-77310", "POL-77310"), calls)
        assertTrue(choice.state.value.checked)
        assertFalse(choice.state.value.missing)
    }

    @Test
    fun givenTheHostCannotAnswer_whenTheChoiceIsSaved_thenItFailsWithoutCiclo() = runBlocking {
        val tokens = TokenStore(context).also { it.clear() }
        tokens.save(SessionTokens("jwt-access", "jwt-refresh", 900))
        val cache = BffCache(context).also { it.clear() }
        val api = BffClients.open("http://127.0.0.1:1", tokens, readTimeoutSeconds = 1).api
        val remote = RemoteRenewalPreferenceRepository(api, BffGate(api, cache))
        assertEquals(RenewalSave.Failed, remote.save("POL-88219-CO", true))
        server.enqueue(MockResponse().setResponseCode(200).setBody("{"))
        assertEquals(RenewalSave.Failed, repository.save("POL-88219-CO", false))
        server.enqueue(MockResponse().setResponseCode(503).setBody("""{"detail":"no"}"""))
        assertEquals(RenewalSave.Failed, repository.save("POL-88219-CO", true))
        assertEquals(RenewalSave.Saved(false), StandInRenewalPreferenceRepository().save("POL-88219-CO", false))
    }

    private fun saved(numero: String, enabled: Boolean) = MockResponse()
        .setResponseCode(200)
        .setHeader("Content-Type", "application/json")
        .setBody("""{"numero":"$numero","renovacionAutomatica":$enabled}""")
}
