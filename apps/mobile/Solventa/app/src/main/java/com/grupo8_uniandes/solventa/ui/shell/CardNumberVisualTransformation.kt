package com.grupo8_uniandes.solventa.ui.shell

import androidx.compose.foundation.text.input.InputTransformation
import androidx.compose.foundation.text.input.OutputTransformation
import androidx.compose.foundation.text.input.TextFieldBuffer
import androidx.compose.foundation.text.input.byValue
import androidx.compose.foundation.text.input.insert
import com.grupo8_uniandes.solventa.domain.issuance.CardFranchise
import com.grupo8_uniandes.solventa.domain.issuance.CardNumber

/**
 * Drops anything past the franchise length before the field can keep it.
 * The string text field would otherwise keep rejected keystrokes.
 */
val CardNumberInput: InputTransformation =
    InputTransformation.byValue { _, proposed ->
        CardNumber.digits(proposed.toString())
    }

object CardNumberOutput : OutputTransformation {
    override fun TextFieldBuffer.transformOutput() {
        val sizes = when (CardNumber.franchise(asCharSequence().toString())) {
            CardFranchise.Amex -> intArrayOf(4, 6, 5)
            CardFranchise.Diners -> intArrayOf(4, 6, 4)
            else -> intArrayOf(4, 4, 4, 4)
        }
        var index = 0
        val breaks = ArrayList<Int>(sizes.size)
        for (size in sizes.dropLast(1)) {
            index += size
            if (index < length) breaks += index
        }
        for (at in breaks.asReversed()) {
            insert(at, " ")
        }
    }
}
