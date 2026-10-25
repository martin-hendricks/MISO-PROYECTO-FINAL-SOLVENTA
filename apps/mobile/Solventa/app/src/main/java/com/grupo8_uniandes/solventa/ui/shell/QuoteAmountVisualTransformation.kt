package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.input.OffsetMapping
import androidx.compose.ui.text.input.TransformedText
import androidx.compose.ui.text.input.VisualTransformation
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatQuoteAmount

class QuoteAmountVisualTransformation(
    private val region: Region,
) : VisualTransformation {
    override fun filter(text: AnnotatedString): TransformedText {
        val formatted = formatQuoteAmount(text.text, region)
        if (formatted.isEmpty()) {
            return TransformedText(AnnotatedString(""), OffsetMapping.Identity)
        }
        return TransformedText(
            AnnotatedString(formatted),
            quoteAmountOffsetMapping(formatted),
        )
    }
}

internal fun quoteAmountOffsetMapping(formatted: String): OffsetMapping {
    val digitIndexes = formatted.mapIndexedNotNull { index, char ->
        if (char.isDigit()) index else null
    }
    return object : OffsetMapping {
        override fun originalToTransformed(offset: Int): Int {
            if (digitIndexes.isEmpty()) return formatted.length
            if (offset <= 0) return digitIndexes.first()
            if (offset >= digitIndexes.size) return formatted.length
            return digitIndexes[offset - 1] + 1
        }

        override fun transformedToOriginal(offset: Int): Int {
            return formatted.take(offset.coerceIn(0, formatted.length)).count { it.isDigit() }
                .coerceIn(0, digitIndexes.size)
        }
    }
}
