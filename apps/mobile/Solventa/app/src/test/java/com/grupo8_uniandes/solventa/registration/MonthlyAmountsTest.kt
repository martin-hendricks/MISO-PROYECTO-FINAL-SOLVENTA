package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.data.bff.dto.SignupDto
import com.grupo8_uniandes.solventa.data.bff.fixture.PublishedSamples
import com.grupo8_uniandes.solventa.data.bff.mapping.bffJson
import com.grupo8_uniandes.solventa.data.bff.mapping.toDto
import com.grupo8_uniandes.solventa.data.bff.mapping.toRecord
import com.grupo8_uniandes.solventa.data.bff.mapping.toRequestElement
import com.grupo8_uniandes.solventa.domain.bff.offer.DeviceRisk
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRecord
import com.grupo8_uniandes.solventa.domain.registration.MonthlyAmounts
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class MonthlyAmountsTest {
    @Test
    fun givenTwoFractionDigits_whenIncomeIsPositiveAndSpendingIsZero_thenThePairIsKept() {
        assertEquals("4500000.00" to "0.00", MonthlyAmounts.pair("4500000.00", "0.00"))
        assertEquals("1500000.00", MonthlyAmounts.spending("1500000.00"))
    }

    @Test
    fun givenAWholeAmountOrAComma_whenChecked_thenItBecomesTwoFractionDigits() {
        assertEquals("4500000.00" to "0.00", MonthlyAmounts.pair("4500000", "0"))
        assertEquals("4500000.00" to "1200000.00", MonthlyAmounts.pair("4.500.000", "1.200.000"))
        assertEquals("4500000.50" to "1200000.00", MonthlyAmounts.pair("4500000,5", "1.200.000,00"))
        assertEquals("12.50", MonthlyAmounts.income("12.5"))
    }

    @Test
    fun givenZeroIncomeOrAMissingFraction_whenChecked_thenThePairIsRejected() {
        assertNull(MonthlyAmounts.income("0.00"))
        assertNull(MonthlyAmounts.income("0"))
        assertNull(MonthlyAmounts.income("-1.00"))
        assertNull(MonthlyAmounts.spending("-0.01"))
        assertNull(MonthlyAmounts.pair("1.00", "1.2.3"))
        assertNull(MonthlyAmounts.pair("  ", "0.00"))
    }

    @Test
    fun givenASignupWithoutAmounts_whenReadBack_thenTheSuccessBodyDoesNotInventThem() {
        val bare = PublishedSamples.SIGNUP
            .replace(""","ingresos_mensuales":"4500000.00","gastos_mensuales":"1500000.00"""", "")
        val echoed = bffJson.decodeFromString(SignupDto.serializer(), bare).toRecord()
        assertEquals("", echoed.ingresosMensuales)
        assertEquals("", echoed.gastosMensuales)
        assertEquals("", echoed.contrasena)
    }

    @Test
    fun givenAmountsOnTheAccount_whenSent_thenTheQuoteRiskDoesNotCarryThem() {
        val sent = SignupRecord(
            nombre = "Camila",
            apellidos = "Restrepo",
            documento = "1012345678",
            correo = "camila@correo.com",
            pruebaDeVida = Liveness.OK,
            habeasData = true,
            ingresosMensuales = "4500000.00",
            gastosMensuales = "1500000.00",
        ).toDto()
        val json = bffJson.encodeToString(SignupDto.serializer(), sent)
        assertTrue(json.contains("ingresos_mensuales"))
        assertTrue(json.contains("gastos_mensuales"))
        assertFalse(json.contains("contrasena\":\"secreto"))
        val risk = DeviceRisk(2_400_000, "apple", false, "iPhone 15").toRequestElement().toString()
        assertFalse(risk.contains("ingresos"))
        assertFalse(risk.contains("gastos"))
    }
}
