package com.grupo8_uniandes.solventa.quote

import androidx.compose.ui.text.AnnotatedString
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.ui.shell.QuoteAmountVisualTransformation
import com.grupo8_uniandes.solventa.ui.shell.quoteAmountOffsetMapping
import org.junit.Assert.assertEquals
import org.junit.Test

class QuoteAmountVisualTransformationTest {
    @Test
    fun givenColombiaDigits_whenShown_thenGroupingStaysInTypedOrder() {
        val shown = QuoteAmountVisualTransformation(Region.Colombia)
            .filter(AnnotatedString("12345678"))
        assertEquals("$12.345.678", shown.text.text)
        val mapping = quoteAmountOffsetMapping(shown.text.text)
        assertEquals(0, mapping.transformedToOriginal(0))
        assertEquals(shown.text.length, mapping.originalToTransformed(8))
        assertEquals(2, mapping.transformedToOriginal(3))
    }

    @Test
    fun givenEachRegion_whenShown_thenSymbolAndSeparatorsFollowTheCountry() {
        assertEquals(
            "$12,345,678",
            QuoteAmountVisualTransformation(Region.Mexico).filter(AnnotatedString("12345678")).text.text,
        )
        assertEquals(
            "$12.345.678",
            QuoteAmountVisualTransformation(Region.Chile).filter(AnnotatedString("12345678")).text.text,
        )
        assertEquals(
            "S/ 12,345,678",
            QuoteAmountVisualTransformation(Region.Peru).filter(AnnotatedString("12345678")).text.text,
        )
    }
}
