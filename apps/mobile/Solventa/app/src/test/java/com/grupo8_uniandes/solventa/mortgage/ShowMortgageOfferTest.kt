package com.grupo8_uniandes.solventa.mortgage

import com.grupo8_uniandes.solventa.domain.bff.mortgage.FirmMortgageOffer
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ShowMortgageOffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ShowMortgageOfferTest {
    @Test
    fun givenTheReviewOffer_whenShown_thenTheFrameLinesAndPremium() {
        val offer = ShowMortgageOffer().show()

        assertEquals("Vida hipotecario · paso 2 de 3", offer.title)
        assertEquals("Vida hipotecario · oferta en firme", offer.heading)
        assertEquals("Protección de pagos · prima según tu perfil", offer.coverage)
        assertEquals(89_500L, offer.prima)
        assertEquals("COP", offer.moneda)
        assertEquals("$89.500 COP / mes", offer.premiumText)
        assertFalse(profilingFields(offer))
    }

    @Test
    fun givenAnotherOffer_whenShown_thenOnlyCoverageAndPremiumChange() {
        val offer = ShowMortgageOffer().show(
            coverage = "Amparo de saldo",
            prima = 12_000L,
            moneda = "COP",
        )

        assertEquals("Vida hipotecario · paso 2 de 3", offer.title)
        assertEquals("Vida hipotecario · oferta en firme", offer.heading)
        assertEquals("Amparo de saldo", offer.coverage)
        assertEquals(12_000L, offer.prima)
        assertEquals("$12.000 COP / mes", offer.premiumText)
        assertFalse(profilingFields(offer))
    }

    private fun profilingFields(offer: FirmMortgageOffer): Boolean {
        return offer.javaClass.declaredFields.any { field ->
            val name = field.name
            name.contains("factor") || name.contains("degrad") || name.contains("consent")
        }
    }
}
