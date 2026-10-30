package com.grupo8_uniandes.solventa.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimStatus
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.ListClaims
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ListClaimsTest {
    @Test
    fun givenTheReviewSet_whenListed_thenEachRowKeepsIdBodyAndStatus() = runBlocking {
        val claims = ListClaims(repo(reviewRows()))()

        val rows = (claims as StandInAnswer.Ready).value
        assertEquals("SIN-441", rows[0].siniestroId)
        assertEquals("Protección de dispositivo · pantalla rota", rows[0].whatHappened())
        assertEquals("En evaluación", rows[0].statusWords())
        assertEquals("SIN-220", rows[1].siniestroId)
        assertEquals("Protección de dispositivo · hurto", rows[1].whatHappened())
        assertEquals("Pagado", rows[1].statusWords())
        assertEquals("SIN-P01", rows[2].siniestroId)
        assertEquals("Clima y vuelos · retraso de vuelo", rows[2].whatHappened())
        assertEquals("Pago automático · pagado", rows[2].statusWords())
    }

    @Test
    fun givenNoClaims_whenListed_thenTheResultIsEmpty() = runBlocking {
        val claims = ListClaims(repo(emptyList()))()

        assertTrue((claims as StandInAnswer.Ready).value.isEmpty())
    }

    @Test
    fun givenAStatusAPushWouldCarry_whenListed_thenTheCardShowsThatStanding() = runBlocking {
        val pushed = ClaimSummary(
            siniestroId = "SIN-P01",
            ramo = "Clima y vuelos",
            resumen = "retraso de vuelo",
            estado = ClaimStatus.PAGADO,
            estadoTexto = "Pago automático · pagado",
        )

        val claims = ListClaims(repo(listOf(pushed)))()

        assertEquals("Pago automático · pagado", (claims as StandInAnswer.Ready).value.single().statusWords())
    }

    @Test
    fun givenAStandingWithoutDisplayText_whenRead_thenTheStatusWordMatchesTheCase() {
        assertEquals("Recibido", summary(ClaimStatus.RECIBIDO).statusWords())
        assertEquals("Decidido", summary(ClaimStatus.DECIDIDO).statusWords())
        assertEquals("Enrutado", summary(ClaimStatus.ENRUTADO).statusWords())
        val drawn = summary(ClaimStatus.EN_EVALUACION)
        assertEquals(null, drawn.estadoTexto)
        assertEquals("En evaluación", drawn.copy(estadoTexto = null).statusWords())
        assertEquals("Pago automático · pagado", drawn.copy(estadoTexto = "Pago automático · pagado").estadoTexto)
    }

    private fun summary(estado: ClaimStatus) = ClaimSummary(
        siniestroId = "SIN-1",
        ramo = "Protección de dispositivo",
        resumen = "pantalla rota",
        estado = estado,
    )

    private fun reviewRows() = listOf(
        ClaimSummary("SIN-441", "Protección de dispositivo", "pantalla rota", ClaimStatus.EN_EVALUACION),
        ClaimSummary("SIN-220", "Protección de dispositivo", "hurto", ClaimStatus.PAGADO),
        ClaimSummary(
            "SIN-P01",
            "Clima y vuelos",
            "retraso de vuelo",
            ClaimStatus.PAGADO,
            "Pago automático · pagado",
        ),
    )

    private fun repo(rows: List<ClaimSummary>) = object : ClaimRepository {
        override suspend fun notify(notice: ClaimNotice): StandInAnswer<ClaimReceipt> = StandInAnswer.Failed

        override suspend fun list(): StandInAnswer<List<ClaimSummary>> = StandInAnswer.Ready(rows)
    }
}
