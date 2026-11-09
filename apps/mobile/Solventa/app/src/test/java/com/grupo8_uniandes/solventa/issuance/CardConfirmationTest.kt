package com.grupo8_uniandes.solventa.issuance

import com.grupo8_uniandes.solventa.data.bff.remote.MobileBffApi
import com.grupo8_uniandes.solventa.domain.issuance.CardConfirmation
import com.grupo8_uniandes.solventa.domain.issuance.CardExpiry
import com.grupo8_uniandes.solventa.domain.issuance.CardFranchise
import com.grupo8_uniandes.solventa.domain.issuance.CardNumber
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CardConfirmationTest {
    @Test
    fun givenACompleteCard_whenChecked_thenOnlyThatShapeIsValid() {
        assertTrue(CardConfirmation.valid("Camila Restrepo", "4242 4242 4242 4242", "08", "28", "123"))
        assertTrue(CardConfirmation.valid("Camila Restrepo", "4242424242424242", "12", "30", "1234"))
        assertTrue(CardConfirmation.valid("Camila Restrepo", "378282246310005", "08", "28", "1234"))
        assertTrue(CardConfirmation.valid("Camila Restrepo", "30569309025904", "01", "28", "123"))
        assertFalse(CardConfirmation.valid("  ", "4242424242424242", "08", "28", "123"))
        assertFalse(CardConfirmation.valid("Camila", "424242424242424", "08", "28", "123"))
        assertFalse(CardConfirmation.valid("Camila", "3782822463100051", "08", "28", "1234"))
        assertFalse(CardConfirmation.valid("Camila", "4242424242424242", "13", "28", "123"))
        assertFalse(CardConfirmation.valid("Camila", "4242424242424242", "00", "28", "123"))
        assertFalse(CardConfirmation.valid("Camila", "4242424242424242", "1", "28", "123"))
        assertFalse(CardConfirmation.valid("Camila", "4242424242424242", "08", "2", "123"))
        assertFalse(CardConfirmation.valid("Camila", "4242424242424242", "08", "28", "12"))
        assertFalse(CardConfirmation.valid("Camila", "4242424242424242", "08", "28", "12345"))
    }

    @Test
    fun givenAValidCard_whenConfirmed_thenTheValuesAreDiscardedAndASecondConfirmDoesNothing() {
        val viewModel = ConfirmacionTarjetaViewModel()
        viewModel.onTitular("Camila Restrepo")
        viewModel.onNumero("4242424242424242")
        viewModel.onMes("8")
        viewModel.onAnio("28")
        viewModel.onCodigo("123")
        assertEquals("08", viewModel.state.value.mes)
        assertEquals("28", viewModel.state.value.anio)
        assertTrue(viewModel.confirm())
        assertEquals("", viewModel.state.value.titular)
        assertEquals("", viewModel.state.value.numero)
        assertEquals("", viewModel.state.value.mes)
        assertEquals("", viewModel.state.value.anio)
        assertEquals("", viewModel.state.value.codigo)
        viewModel.onTitular("Otra")
        assertFalse(viewModel.confirm())
        assertEquals("", viewModel.state.value.titular)
    }

    @Test
    fun givenAShortNumber_whenConfirmIsTapped_thenNothingStarts() {
        val viewModel = ConfirmacionTarjetaViewModel()
        viewModel.onTitular("Camila")
        viewModel.onNumero("4242")
        viewModel.onMes("08")
        viewModel.onAnio("28")
        viewModel.onCodigo("123")
        assertFalse(viewModel.confirm())
        assertEquals("4242", viewModel.state.value.numero)
    }

    @Test
    fun givenTheScreenIsLeft_whenDiscarded_thenNothingIsKeptAndIssuanceDoesNotStart() {
        val viewModel = ConfirmacionTarjetaViewModel()
        viewModel.onNumero("4242424242424242")
        viewModel.discard()
        assertEquals("", viewModel.state.value.numero)
        assertFalse(viewModel.state.value.canConfirm)
    }

    @Test
    fun givenAPrefix_whenGrouped_thenTheFranchiseSetsTheGapsAndTheLength() {
        assertEquals(CardFranchise.Visa, CardNumber.franchise("4242424242424242"))
        assertEquals("4242 4242 4242 4242", CardNumber.grouped("4242424242424242"))
        assertEquals(CardFranchise.Mastercard, CardNumber.franchise("5555555555554444"))
        assertEquals("5555 5555 5555 4444", CardNumber.grouped("5555555555554444"))
        assertEquals(CardFranchise.Amex, CardNumber.franchise("378282246310005"))
        assertEquals("3782 822463 10005", CardNumber.grouped("378282246310005"))
        assertEquals("378282246310005", CardNumber.digits("3782822463100059"))
        assertEquals(CardFranchise.Diners, CardNumber.franchise("30569309025904"))
        assertEquals("3056 930902 5904", CardNumber.grouped("30569309025904"))
        assertEquals(CardFranchise.Amex, CardNumber.franchise("341111111111111"))
        assertEquals(CardFranchise.Diners, CardNumber.franchise("36123456789012"))
        assertEquals(CardFranchise.Diners, CardNumber.franchise("38123456789012"))
        assertEquals(CardFranchise.Diners, CardNumber.franchise("30012345678901"))
        assertEquals(CardFranchise.Mastercard, CardNumber.franchise("2221000000000000"))
        assertEquals(CardFranchise.Unknown, CardNumber.franchise("1"))
        assertEquals(CardFranchise.Unknown, CardNumber.franchise(""))
        assertEquals("", CardNumber.grouped(""))
        assertEquals("", CardNumber.grouped("abcd"))
        assertEquals("4", CardNumber.grouped("4"))
        assertEquals(14, CardNumber.limit("36"))
        assertEquals(16, CardNumber.limit("4"))
        assertEquals("4242", CardNumber.digits("42ab42"))
        assertEquals("08", CardExpiry.month("8"))
        assertEquals("12", CardExpiry.month("12"))
        assertEquals("1", CardExpiry.month("13"))
        assertEquals("28", CardExpiry.year("281"))
    }

    @Test
    fun givenAcceptQuote_whenInspected_thenItHasNoCardBody() {
        val method = MobileBffApi::class.java.methods.first { it.name == "acceptQuote" }
        val types = method.parameterTypes.map { it.simpleName }
        assertFalse(types.any { it.contains("Card") || it.contains("Body") || it == "RequestBody" })
        assertTrue(types.contains("String"))
    }
}
