package com.grupo8_uniandes.solventa.prestadores

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceResult
import com.grupo8_uniandes.solventa.domain.bff.assistance.ClaimProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.FindProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderArea
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCenter
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderCity
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderPage
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderQuery
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderType
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class FindProvidersTest {
    @Test
    fun givenDistances_whenSearching_thenTheNearerProviderIsFirst() = runBlocking {
        val repo = RecordingAssistance(
            page = StandInAnswer.Ready(
                ProviderPage(
                    centro = ProviderCenter(4.64, -74.06, "posicion"),
                    radioKm = 10.0,
                    prestadores = listOf(sample("far", 3.4), sample("near", 0.9)),
                ),
            ),
        )
        val page = (FindProviders(repo).search(ProviderQuery(lat = 4.64, lng = -74.06, ramo = "soat-motocicleta", radioKm = 10.0)) as StandInAnswer.Ready).value

        assertEquals("near", page.prestadores[0].id)
        assertEquals("far", page.prestadores[1].id)
        assertEquals(4.64, repo.lastQuery!!.lat!!, 0.0)
        assertEquals(-74.06, repo.lastQuery!!.lng!!, 0.0)
        assertEquals("soat-motocicleta", repo.lastQuery!!.ramo)
        assertEquals(10.0, repo.lastQuery!!.radioKm!!, 0.0)
        assertNull(repo.lastQuery!!.ciudad)
    }

    @Test
    fun givenACity_whenSearching_thenDistanceStaysNull() = runBlocking {
        val city = sample("PRE-BOG-06", null)
        val repo = RecordingAssistance(
            page = StandInAnswer.Ready(
                ProviderPage(ProviderCenter(4.6, -74.08, "ciudad"), 10.0, listOf(city)),
            ),
        )
        val page = (FindProviders(repo).search(ProviderQuery(ciudad = "Bogotá", radioKm = 10.0)) as StandInAnswer.Ready).value

        assertEquals("Bogotá", repo.lastQuery!!.ciudad)
        assertNull(repo.lastQuery!!.lat)
        assertNull(page.prestadores.single().distanciaKm)
    }

    @Test
    fun givenAClaim_whenAsked_thenTheIdIsForwarded() = runBlocking {
        val repo = RecordingAssistance(
            claim = StandInAnswer.Ready(
                ClaimProviders(
                    siniestroId = "SIN-1",
                    numero = "SIN-1988",
                    ramo = "soat-motocicleta",
                    ramoFijo = "soat-motocicleta",
                    sinGeoetiqueta = true,
                    centro = null,
                    radioKm = 10.0,
                    prestadores = emptyList(),
                ),
            ),
        )
        val area = ProviderArea(4.66, 4.62, -74.05, -74.08)
        val page = (FindProviders(repo).nearClaim("SIN-1", area) as StandInAnswer.Ready).value

        assertEquals("SIN-1", repo.lastClaimId)
        assertEquals(area, repo.lastClaimArea)
        assertEquals(true, page.sinGeoetiqueta)
        assertEquals("SIN-1988", page.numero)
    }

    @Test
    fun givenACountry_whenCitiesAreAsked_thenThePaisIsForwarded() = runBlocking {
        val repo = RecordingAssistance()
        val cities = (FindProviders(repo).cities("PE") as StandInAnswer.Ready).value

        assertEquals("PE", repo.lastPais)
        assertEquals("Lima", cities.single().nombre)
    }

    @Test
    fun givenTheCatalogFails_whenSearching_thenTheFailureIsReturned() = runBlocking {
        val find = FindProviders(RecordingAssistance())

        assertTrue(find.search(ProviderQuery()) is StandInAnswer.Failed)
        assertTrue(find.nearClaim("SIN-1") is StandInAnswer.Failed)
    }
}

internal fun sample(id: String, distanciaKm: Double?) = Provider(
    id = id,
    nombre = "Taller Moto Chapinero",
    tipo = ProviderType.TALLER_MOTOS,
    ramos = listOf("soat-motocicleta"),
    direccion = "Cra 13 #45-18",
    ciudad = "Bogotá",
    barrio = "Chapinero",
    lat = 4.6355,
    lng = -74.0655,
    telefono = "601 555 0112",
    horario = "Lun–Sáb 7:00–19:00",
    distanciaKm = distanciaKm,
)

private class RecordingAssistance(
    private val page: StandInAnswer<ProviderPage> = StandInAnswer.Failed,
    private val claim: StandInAnswer<ClaimProviders> = StandInAnswer.Failed,
) : AssistanceRepository {
    var lastQuery: ProviderQuery? = null
    var lastClaimId: String? = null
    var lastClaimArea: ProviderArea? = null
    var lastPais: String? = null

    override suspend fun providers(query: ProviderQuery): StandInAnswer<ProviderPage> {
        lastQuery = query
        return page
    }

    override suspend fun cities(pais: String): StandInAnswer<List<ProviderCity>> {
        lastPais = pais
        return StandInAnswer.Ready(listOf(ProviderCity("Lima", -12.0464, -77.0428, 11, 5)))
    }

    override suspend fun providersNearClaim(id: String, area: ProviderArea?): StandInAnswer<ClaimProviders> {
        lastClaimId = id
        lastClaimArea = area
        return claim
    }

    override suspend fun request(body: AssistanceRequest): StandInAnswer<AssistanceResult> = StandInAnswer.Failed
}
