package com.grupo8_uniandes.solventa.prestadores

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.assistance.FindProviders
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderPage
import com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderQuery
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test

class PrestadorFichaViewModelTest {
    @Test
    fun givenAProvider_whenDirectionsAreAsked_thenTheUriUsesItsCoordinates() = runBlocking {
        val provider = sample("PRE-BOG-06", 0.9)
        val find = FindProviders(
            object : com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository {
                override suspend fun providers(query: ProviderQuery) = StandInAnswer.Ready(
                    ProviderPage(centro = null, radioKm = 10.0, prestadores = listOf(provider)),
                )

                override suspend fun cities(pais: String) = StandInAnswer.Failed

                override suspend fun providersNearClaim(
                    id: String,
                    area: com.grupo8_uniandes.solventa.domain.bff.assistance.ProviderArea?,
                ) = StandInAnswer.Failed

                override suspend fun request(body: com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest) =
                    StandInAnswer.Failed
            },
        )
        find.search(ProviderQuery(ciudad = "Bogotá"))
        val viewModel = PrestadorFichaViewModel("PRE-BOG-06", find)

        assertEquals(
            "https://www.google.com/maps/dir/?api=1&destination=4.6355,-74.0655",
            viewModel.directionsUri(),
        )
    }
}
