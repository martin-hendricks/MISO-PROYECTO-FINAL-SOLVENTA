package com.grupo8_uniandes.solventa.mortgage

import com.grupo8_uniandes.solventa.data.bff.dto.HomeDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageOutDto
import com.grupo8_uniandes.solventa.data.bff.mapping.decode
import com.grupo8_uniandes.solventa.data.bff.mapping.toHome
import com.grupo8_uniandes.solventa.data.bff.mapping.toQuote
import com.grupo8_uniandes.solventa.data.home.StandInHomeRepository
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.home.BffHome
import com.grupo8_uniandes.solventa.domain.bff.home.HomeBffRepository
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageCredit
import com.grupo8_uniandes.solventa.domain.home.LoadInicio
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class MortgageCreditTest {
    @Test
    fun givenAPendingOrigination_whenHomeIsRead_thenItCarriesTheCredit() {
        val home = decode<HomeDto>(
            """
            {"ofertaVigente":null,"poliza":null,"siniestroEnCurso":null,
             "hipotecario":{"estado":"disponible","valor":180000000,"plazoMeses":180,"origen":"socio"}}
            """,
        )!!.toHome()

        assertEquals(MortgageCredit(valor = 180_000_000L, plazoMeses = 180), home.hipotecario)
    }

    @Test
    fun givenNoOrigination_whenHomeIsRead_thenThereIsNoCredit() {
        val home = decode<HomeDto>(
            """{"ofertaVigente":null,"poliza":null,"siniestroEnCurso":null,"hipotecario":null}""",
        )!!.toHome()

        assertNull(home.hipotecario)
    }

    @Test
    fun givenAQuotedOffer_whenRead_thenItKeepsTheQuoteIdCoverageAndDecimalPremium() {
        val quote = decode<MortgageOutDto>(
            """
            {"cotizacionId":"COT-77","ramo":"Vida hipotecario",
             "descripcion":"Cubre el saldo del crédito hipotecario durante el plazo pactado.",
             "estado":"oferta_vigente","prima":"106900.00","moneda":"COP",
             "factores":["zona_riesgo"],"degradada":false}
            """,
        )!!.toQuote()

        assertEquals("COT-77", quote.cotizacionId)
        assertEquals(106_900L, quote.prima)
        assertEquals("Cubre el saldo del crédito hipotecario durante el plazo pactado.", quote.descripcion)
    }

    @Test
    fun givenThePublishedSample_whenRead_thenItStillDecodesWithoutAQuote() {
        val quote = decode<MortgageOutDto>(
            """{"ramo":"Vida hipotecario","estado":"oferta_vigente","prima":64000,"moneda":"COP","factores":[],"degradada":false}""",
        )!!.toQuote()

        assertNull(quote.cotizacionId)
        assertEquals(64_000L, quote.prima)
    }

    @Test
    fun givenACredit_whenInicioIsSelected_thenTheCardCarriesIt() {
        val credit = MortgageCredit(valor = 180_000_000L, plazoMeses = 180)

        val withCredit = LoadInicio(StandInHomeRepository(home(credit))).panel()!!
        val without = LoadInicio(StandInHomeRepository(home(null))).panel()!!

        assertTrue(withCredit.vidaCrediticia)
        assertEquals(credit, withCredit.mortgageCredit)
        assertFalse(without.vidaCrediticia)
        assertNull(without.mortgageCredit)
    }

    private fun home(credit: MortgageCredit?) = object : HomeBffRepository {
        override suspend fun load(): StandInAnswer<BffHome> =
            StandInAnswer.Ready(BffHome(null, null, null, credit))
    }
}
